---
title: "Road to CKAD"
date: 2023-10-13T00:00:00+02:00
draft: false
tags: ["Kubernetes", "Homelab", "Certification"]
author: "Simen Røstvik"
ShowToc: true
description: "My adventure in Certifying myself in Kubernetes"
cover:
  image: "images/captain.jpg"
  alt: "A captain overseeing his ship"
  source: https://unsplash.com/photos/tOJDsuU9MlE
---

## So I took some certs

Ive recently gone trough the Kubernetes Administrator, Developer and Security Specialist certifications. In typical fashion I broke some stuff on my way to get there.

{{< note type="note" >}}
The git references in this article are not up-to-date, as later deployments has made me consolidating multiple repos to a single infra repo.
{{< /note >}}

## Preparation

This is everything I used to prepare for these certifications:

- Time
- Some smol computing boys, three Raspberry PI 4 8GB was hurt for this blogpost
- Lectures with practical tests, I went with the courses from KodeKloud
- A not so big LXC running on Proxmox 7
- Patience
- Time

### Proxmox and LXC

For some unrelated infrastructure, I set up Proxmox. I attempted to put most of the configuration in Ansible, but its just not feasible in the long run. The Proxmox host is however not fully ClickOps based, as packages, swap and [the certificate(fetched from OpnSense)](https://git.roxedus.dev/Roxedus/Infra/src/commit/946284e0bed7a334949755be45cfcb9b55a7e881/ansible/roles/proxmox/templates/get_cert.sh.j2) is managed by the playbook.

#### Controlplane LXC

Because sourcing additional Raspberry PI's was an impossible task (and still isn't easy), I thought "Hey, my Proxmox host is only doing Home-Assistant right know, I can squeeze more onto it".

Since I am who I am, I decided to dabble in something new, enter Linux Containers(lxc)[^1].

The reason for researching this method is straightforward; VMs are heavy, OCI[^2] containers are light. I needed something in between.
This host is limited on resources, but not starved for them. Therefore avoiding running another kernel and subsystem would be preferred, this ruled out Virtual Machines.
Another option I am very comfortable with, is Docker. However, (stock) Kubernetes really wants a fully-fledged init system running and I am not crazy enough to run a complete Systemd instance in a Docker container.

As it took multiple attempts to get the LXC configured to make kubeadm happy, I saved that file once all the issues was ironed out. It looks something like this:

```yml
arch: amd64
cores: 2
hostname: controlplane
memory: 4096
net0: name=eth0,bridge=vmbr0,firewall=1,gw=<gateway ip>,hwaddr=<mac>,ip=<ip with cidir range>,type=veth
ostype: ubuntu
rootfs: <DiskInfo>,size=50G
searchdomain: kube.<domain>
swap: 0
features: fuse=1,mount=nfs,nesting=1
lxc.apparmor.profile: unconfined
lxc.cap.drop:
lxc.cgroup.devices.allow: a
lxc.mount.auto: proc:rw sys:rw
```

I later tried to define this LXC with Terraform, but ran mostly into auth issues. This LXC needed to be privileged, which means it cannot be created by anyone else then the "root" user, making a service account useless. I have also opted for using MFA on the root account, which made user/password moot.

### Playing with the playbook

As mentioned, I have a Ansible playbook for infrastructure running inside my lan. This playbook gives me a familiar and uniform environment for all hosts.
It handles [common packages](https://git.roxedus.dev/Roxedus/Infra/src/commit/946284e0bed7a334949755be45cfcb9b55a7e881/ansible/group_vars/all.yml#L21-L37) I have come to expect being present on the machine im working on, while setting up [my user with a public key](https://git.roxedus.dev/Roxedus/Infra/src/commit/946284e0bed7a334949755be45cfcb9b55a7e881/ansible/tasks/users.yml), and the [prompt in my shell](https://git.roxedus.dev/Roxedus/Infra/src/commit/946284e0bed7a334949755be45cfcb9b55a7e881/ansible/tasks/omp.yml).

To get my environment ready, I wrote a Kubernetes role into my existing [Ansible Infra playbook](https://git.roxedus.dev/Roxedus/Infra/src/commit/946284e0bed7a334949755be45cfcb9b55a7e881/ansible/roles/kubernetes), this takes care of both [Kubeadm's](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/#before-you-begin) and Kubernetes' requirements.
This includes [disabling swap](https://git.roxedus.dev/Roxedus/Infra/src/commit/946284e0bed7a334949755be45cfcb9b55a7e881/ansible/roles/kubernetes/tasks/node.yml#L1-L14), setting up [containerd as a runtime](https://git.roxedus.dev/Roxedus/Infra/src/commit/946284e0bed7a334949755be45cfcb9b55a7e881/ansible/run.yml#L134-L138)(thanks [Jeff](https://github.com/geerlingguy/ansible-role-containerd)) and a whole lot of [kernel tuning](https://git.roxedus.dev/Roxedus/Infra/src/commit/946284e0bed7a334949755be45cfcb9b55a7e881/ansible/roles/kubernetes/tasks/node.yml#L80-L115). Using some roles in the Ansible Galaxy might have saved me some time here, but before I landed on using Jeff's containerd role, I tried to use some of the cri-o roles, but I spent too much time digging in apt repos to mitigate the fact that Kubernetes with ARM64 nodes is less adopted than I thought(more on this later). I quickly abandoned the idea of using a Galaxy role for cri-o, after struggling to get cri-o going at all, I gave up on cri-o altogether and settled for the containerd role.

Since my lab is run on somewhat unconventional setups, I had to make several changes for [Raspberry PIs](https://git.roxedus.dev/Roxedus/Infra/src/commit/946284e0bed7a334949755be45cfcb9b55a7e881/ansible/roles/kubernetes/tasks/node.yml#L42-L63) such as enabling Cgroups and setting the GPU memory size. As well for some [enabling KMSG in the LXC](https://git.roxedus.dev/Roxedus/Infra/src/commit/946284e0bed7a334949755be45cfcb9b55a7e881/ansible/roles/kubernetes/tasks/node.yml#L27-L38).
While all this was working fine in its current state, I wanted to move this lab to a vlan, to segment lab ip range from the proper lan(using a vlan with crosstalk, so no isolation). In Proxmox this is a few straightforward checkboxes, and a textfield, for the Raspberries, this would become harder than it needed to be. In Ubuntu 21.10 they removed the `linux-modules-extra-raspi` package from the base image, this meant that the kernel module 802.1q was not able to be loaded, and thus no vlan. I did a digression into HashiCorp's Packer to determine if it would be worth it to bundle this myself, it wasn't. While I really wanted the playbook to do it all, it now meant I had to ssh into the two nodes after the initial playbook run. I did help myself here, as I bootstrapped the Raspberries with a [`network-config` file](https://git.roxedus.dev/Roxedus/Infra/src/commit/946284e0bed7a334949755be45cfcb9b55a7e881/cloud-init/arm-ubuntu/network-config) already set up with the wanted network configuration, all I had to do after the initial run was to alter this file on the host, setting dhcp to false on the untagged interface.

Could I have done this in Ansible? yes. Did I want to? no, I already locked myself out too many times writing this playbook.

---

## Kubeadm init

Now that the nodes OS is provisioned, and kubelets are running, it was time to set up the kubernetes cluster. I choose to go with Kubeadm for bootstrapping the cluster, simply because it's easier than ["the hard way"](https://github.com/kelseyhightower/kubernetes-the-hard-way), and tested in production systems.

Before running the command, you need to make some decisions on networking, as certain solutions need Kubeadm to make changes to its configuration.

Since the LXC is going to be the controlplane, that's where I initialize the cluster. Proxmox's kernel isn't fully compatible with the requirements Kubeadm has set, so the cluster had to be initialized by bypassing the check for the `config` kernel setting.

```text
[ERROR SystemVerification]: failed to parse kernel config: unable to load kernel module: "configs", output: "modprobe: FATAL: Module configs not found in directory /lib/modules/5.15.30-2-pve", err: exit status 1
```

The command I ended up using was

```sh
kubeadm init --pod-network-cidr=10.244.0.0/16 --ignore-preflight-errors=SystemVerification
```

In the output of the init command, I made a note of the join command. The output also tell you that now time is the time to get a CNI[^3], once again I went the easy route with [Flannel](https://github.com/flannel-io/flannel), as it just works out of the box. For my next iteration I am considering [Weave](https://github.com/weaveworks/weave), due to it supporting network policies.

The output helpfully gives you a copy-paste of the commands you need to do if you want to interface with the cluster outside of the root account, the file in this example is also the file you want to have on the computer you plan to manage the cluster by(or you can already here look at creating a dedicated certificate, rather than the one Kubeadm generates).

The next step was running the command with the join token I noted earlier on the other nodes, this should be a painless process. It was, I was now watching the command `kubectl get nodes`, and looking at all the nodes getting to a ready state, it took some convincing, but after a couple of test pods also going into ready state I now had a working cluster.

## GitOps

Because I also had video lectures with practice tests I was doing at the same time, I were already comfortable with kubectl and dealing with bare manifests. I had no desire to do that in this lab, I therefore dove head first into Helm[^4] and Argo CD[^5].

{{< note type="tip" >}}
This section is going to be a bit messy, as I will be linking different commits, from a git-tree that has been rewritten( to remove my previous attempt at trying this, having no idea what I was doing). This is why the first commit has a structure, and a bunch of files.
{{< /note >}}

### Getting started

I installed the Helm binary and went to town. I created a namespace for Argo, then I installed it trough the chart, specifying the namespace. My next step was looking into how I could have Argo manage itself, I quickly discovered the ["App of apps" pattern](https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/), realizing my initial deployment could have been done smoother. I then tore down the deployment and followed the Helm example in Argos docs, [creating the subchart](https://git.roxedus.dev/Roxedus/Argo/src/commit/91cd43c740385e62c9318a19010fb699520d7ac3/Charts/argo-cd)(if you for some reason are following along, you need to pull down the chart locally before you can install it). The install command is now a bit different, as I am using a local chart folder.

```sh
helm install argo-cd Charts/argo-cd/ --namespace argo-cd
```

This chart has some values in `values.yaml` I remember struggling with in my first attempt. I disable dex, as I have no need for external authentication to Argo at the moment. I told the chart to change the service type to nodeport, mainly because I didn't feel like setting up the kubectl port-forward each time I want to look at it. I created another admin account with the Roxedus username (to set the password, you need to use the argo cli/api to reset it with another admin account). As I have no method to generate tls certificates, Argo gets the `--insecure` argument which tells it to allow unencrypted access to the page. Note the comment at the bottom, in my first attempt at this, Argo had some issues with it's pipeline regarding [building and pushing for arm64](https://github.com/argoproj/argo-cd/issues/8394).

The [next commit](https://git.roxedus.dev/Roxedus/Argo/commit/1cbd509a7669370da22261281eeb645eefe97bad) does a couple of things, but I am mainly focusing on [apps subfolder](https://git.roxedus.dev/Roxedus/Argo/src/commit/1cbd509a7669370da22261281eeb645eefe97bad/apps) for the moment. In this folder, I define the `root` application, thanks to Argos application custom resource. The important bit here, is `apps/templates/argo-cd.yaml`, it tells Argo to create a internal application, to track a subfolder in git, this is the same git repository in which the ArgoCD helm subchart lives. Once I tell Argo to watch this apps folder, I can do all creation and destruction of deployments trough git. There is a couple of ways to tell Argo on how to watch this repository, you can use `kubectl` to apply a manifest, using the `argocd` cli, or the easy way, trough the webui. There wasn't much info needed to fill here, just the repo url, and optionally a subfolder. To keep some order, I decided to keep all application definitions in a `apps` folder. Once this was created, I immediately saw it pick up the Argocd chart, and it started to do a couple of remediations, as it had deviated a bit from the initial install.

### Keeping updated

In the same commit as the one deploying the Argo chart, there is also a cronjob definition for [Renovatebot](https://renovatebot.com/), which is a tool for checking a git repository for new version numbers. As the Argo subchart is using a specific version tag, and Renovate speaking Helm repos, Renovate is able to see that there is a new version. It then creates a pull-request on my git repo to update this file to the new version.

The image Renovate publish as default has all the tooling it needs in order to parse and understand all the package systems it knows, this makes it very large, the image is 1.3 GB *compressed*. The alternate `slim` tag only contains node, and relies on the ability to spin up additional containers in order to load tooling.
Because it holds all the tooling, it also makes it unwieldy to offer in multiple architectures, I needed to allow it to run on the one amd64 machine in this cluster, the controlplane. Therefore the job is set to run on nodes with the built-in architecture label, however this is not enough, as controlplanes are by default not allowed to run workloads, you need to tell the workload it is allowed to run on the controlplane, this is done with tolerations.

This cronjob got [deployed](https://git.roxedus.dev/Roxedus/Argo/src/commit/d17fb849fa7071bfec272624c07c7d722fba6a99/apps/templates/ci.yaml) in a "CI" application in Argo, because I figured having a dedicated namespace for CI might be beneficial in the future.

Unlike linitng-tools and other project-specific tools, Renovate is [quite flexible](https://docs.renovatebot.com/configuration-options/#configuration-options) with the location and naming of its project-specific configuration, I choose to call it `.renovaterc`. This file evolved a little of the span of this journey, but it mostly stayed the same, set to watch over pure Kubernetes manifests, Helm charts and Argo-cd.

It is very easy to track changes, and updates I have approved(merged) or declined(closed) in [Gitea](https://git.roxedus.dev/Roxedus/Argo/pulls?q=&type=all&sort=&state=closed&labels=&milestone=0&assignee=0&poster=3).

## Additional Infrastructure

I consider many of the objects in this section as "meta-objects", objects that needs to exist, but does not directly tie into a deployment or application.

### Connecting people

Any good homelab these days will result in some webguis you may want to use in order to keep in track with the current state of the lab, this one is no different. This desire spawned many questions and failed solutions, yet trough all the failed attempts, I managed to keep Traefik as a constant in this endeavour.

The first and simple solution I had in mind was using Cloudflare tunnels to handle external traffic. This was working, but relied on me manually creating tunnels, and cloudflare being in charge of managing TLS, which I don't love.

The next solution is based on a neat project, [justmiles/traefik-cloudflare-tunnel](https://github.com/justmiles/traefik-cloudflare-tunnel/tree/master). It does exactly the steps I previously did manually, but this does it programmatically, and by reading the Traefik routes. Being on arm64 really started hurting here, as cloudflared[^6] at the time did not build images for arm (Traefik-cloudflare-tunnel still doesn't, February 2023). This lead to another tangent, as I cobbled together some build stuff using Github Actions and QEMU to build these projects for arm, all while not modifying the source. This was all done using docker-bake, in my [pipelines repo](https://github.com/Roxedus/pipelines).

**None of these solutions is using the ingress mechanism in Kubernetes, so I kept on looking.**

Being inspired by [this post](https://theorangeone.net/posts/exposing-your-homelab/) by TheOrangeOne, I decided to try rearchitecting the reverse-proxy solution running on my mediaserver, to be fronted by HAProxy for the SNI routing abilities, but I just couldn't befriend using the proxy protocol in nginx.

After coming to the realization that I will always be connected to my lan, thanks to Wireguard, I came to the conclusion of not needing to get to the cluster from the outside. This opened a new avenue of trial and error, mostly to get Traefik to listen to port 80 and 443. I went into this challenge knowing the prerequisites to get this going in Docker and plain Debian. To do this in Kubernetes, you need to tell the pod to attach to the host network, as well as to tell the process to run as root and setting sysctls. I used this setup for a while, but I was not happy having to deal with using host networking. As a side-note this also had me labeling nodes which had the dns set up.

#### Little loadbalancer that could

The final solution depends on [Metallb](https://metallb.universe.tf/) to do the heavy work. If your cluster is not in a cloud, this will do wonders for your load-balancer woes. It has a couple of working-modes, BGP or ARP(layer 2), in my lab it is working with ARP, as none of the [listed limitations](https://metallb.universe.tf/concepts/layer2/#limitations) applies to my use-case. I set it up with [9( or is it 10?) IPs](https://git.roxedus.dev/Roxedus/Argo/src/commit/58554ecda85d965d54f86e105d8990072fdc6d3c/MetaObjects/metallb-pool.yml). Once this was setup, I was now able to create loadbalancer services in my cluster. This allowed me to revert the changes making Traefik running as root, and all the [other changes](https://git.roxedus.dev/Roxedus/Argo/commit/fc69303300f8c94614c183d488ea057dfe6a947a) I needed previously.

### Saving to disk

One of my biggest gripe about kubernetes (or any distributed compute in general) is storage, for many of the applications you want to run, NFS is suitable, however a decent amount of the applications I am interested to eventually run in a cluster does not work well with NFS. There is a lot of solutions to this, some use a host path and lock the pod to that node, others still want to use NFS, I went for [Longhorn.io](https://longhorn.io/) which replicates files in mounts across hosts, allowing pods to migrate between nodes. Longhorn exposes a StorageClass which is a native kubernetes concept I can deal with.

### Managing certificates

While I relied on Traefik's way to handle and generate certificates, and had no problems with this, I was looking into more and more potential applications that works against the tls type of kubernetes secrets. This type was something I had in mind after looking into Traefik's IngressRoute CRD against it's kubernetes ingress integration. At this point I also told myself I was done using shortcuts like IngressRoute when theres built-in functionality.

The helm chart itself is pretty standard, I didn't have to specify much, just some [Cloudflare-specific dns stuff](https://git.roxedus.dev/Roxedus/Argo/src/commit/58554ecda85d965d54f86e105d8990072fdc6d3c/apps/templates/cert-manager.yaml#L23-L24)(This has to be a LeGo thing, as this also needed for Traefik), all the configuration I needed was provisioning a [Cloudflare-issuer](https://cert-manager.io/docs/configuration/acme/dns01/cloudflare/), you tell this spec [which secret](https://git.roxedus.dev/Roxedus/Argo/src/branch/main/MetaObjects/cert-manager-issuer.yml) it should get the api token from.

Like any sane person, I thought testing against the very application I need to revert the change was the best fit, so I went ahead and enabled ingress as well as cert-generation at the [same time](https://git.roxedus.dev/Roxedus/Argo/commit/610e01fe3d569ffe173256fb3471cbdb40b3026d) to Argo, while hoping this didn't lock me out.

I checked the status of the certificate request and order this triggered, to see if it generated a certificate, and sure enough, the order was fulfilled and Traefik used the certificate to serve the Argo subdomain.

```sh
$ kubectl get certificaterequests.cert-manager.io -n argo-cd
NAME                          APPROVED   DENIED   READY   ISSUER                   REQUESTOR                                         AGE
argo-roxedus-com-cert-qzwf2   True                True    roxedus.com-cloudflare   system:serviceaccount:cert-manager:cert-manager   7d
```

```sh
$ kubectl get orders.acme.cert-manager.io -n argo-cd
NAME                                     STATE   AGE
argo-roxedus-com-cert-qzwf2-3069573698   valid   7d
```

### Keeping secrets

Kubernetes secrets are stored in etcd [as plaintext by default](https://kubernetes.io/docs/concepts/configuration/secret/), which in my lab isn't really that big of a deal, but it is something I wanted to prevent if I could. Before starting on this adventure I have always wanted to get some hands-on with HashiCorp Vault, so it was the obvious choice when I needed a secrets manager. Deployment was a breeze, just tell the chart what type of storage class to use, and we are of to the races. I then configured Vault to use kubernetes as a authentication method with [short lived tokens](https://developer.hashicorp.com/vault/docs/auth/kubernetes#how-to-work-with-short-lived-kubernetes-tokens).

I could have used Vault's [injector](https://developer.hashicorp.com/vault/docs/platform/k8s/injector), but I choose to look for a solution that presents native kubernetes objects in the end, this way I can introduce new applications with less changes to helm charts. This is where [external-secrets.io](https://external-secrets.io/) comes into play. Much like the Cert Manager chart, there was not much needed in the helm values, as most configuration happens in dedicated manifests.

For external-secrets to create a kubernetes secret, one would need to create a [ExternalSecret](https://git.roxedus.dev/Roxedus/Argo/src/commit/7809f69c914e26a8b5efee600ff5f585a8962496/MetaObjects/cloudflare-keys.yml) object telling the operator which key and property the secret has in Vault, and to which name the kubernetes secret should have, and optionally which namespace this should target. The ExternalSecret require a SecretStore (or optionally a [ClusterSecretStore](https://git.roxedus.dev/Roxedus/Argo/src/commit/7809f69c914e26a8b5efee600ff5f585a8962496/MetaObjects/secret-store.yml)) to tell the operator about the external secret manager, and how to authorize against the manager, which in this case is trough the short lived tokens.

## My first deployment

Although SearXNG is the first deployment I did outside of helm, it took shape over multiple iterations, as my portfolio of meta-objects evolved. The first version of this used only a NodePort service and a ConfigMap to accompany the deployment. It's [history](https://git.roxedus.dev/Roxedus/Argo/commits/commit/076cbdf6a2a0f659ca7ecb169b0cc3f1ec15c75f/Deployments/searxng.yaml) is a good representation of how this whole cluster evolved, as I used this as my test application. It includes changes like using the Traefik [IngresRoute CRD](https://git.roxedus.dev/Roxedus/Argo/commit/e6eb73947578ccfae672963782f61a7be862af64) to migrating to [Ingress](https://git.roxedus.dev/Roxedus/Argo/commit/fa445c91f64fcd604ec79e22c34d856fa30563f0).

---

## Come certification

After finishing the courses on KodeKloud, as well as building this cluster, I was content with my skills against the outlined areas in the [CKA](https://github.com/cncf/curriculum/blob/master/old-versions/CKA_Curriculum_v1.26.pdf) curriculum, and went ahead to do a run in [KillerShell](https://killer.sh/)(you get two runs in this simulator with the purchase of the exam trough Linux Foundation). It's a good thing this simulator is supposed to be more challenging than the exam, because I was starting to question my skills, regardless, I went ahead and scheduled the exam for a friday, as this was a slow day in my calendar. When I exited the room after submitting my answers, I did not have high hopes, but was still exited to get the result within 24 hours, worst case I could schedule my included second attempt.

While minding my own business, cleaning my apartment, the email came, I passed the exam! I was surprised I managed to land this without much "real world" experience.

I started the following week being quite happy with the achievement from last week, I had set a goal to get CKA and CKAD done by March, and was half-way already in January. We were multiple people at the office going trough different certifications, since the atmosphere still was set on certifications, I figured I should at least look at the curriculum for CKAD, and they looked quite manageable. On Tuesday I was back on the course-grind, by Thursday I had started a run on KillerShell, this time for CKAD.

On Monday I scheduled the CKAD exam for the following day, I was quite confident, as the [curriculum](https://github.com/cncf/curriculum/blob/master/old-versions/CKAD_Curriculum_v1.26.pdf) overlaps a great deal with the CKA, and the fact that I had unknowingly done a lot of the tasks the CKAD focuses on in my own cluster. Tuesday went, and my confidence were still present while leaving the room.

The wait for this email was a bit more nerveracking, mostly because I couldn't be irresponsible by gaming/sleep trough most of the hours, like I could over the weekend. The overall wait time also ended up being a while longer, but it finally came. I passed this one too! I almost expected to pass this one, but it was very comforting receiving confirmation.

Now work started picking up pace, so I had to shift my focus towards other stuff for a while.

As the summer vacation began to close in, work slowed down, I could now focus some more on certifications.

I had one goal for the summer, which was CKS, I was mentally prepared for a month of heavy, and probably demotivating learning. For this certification I also decided to stick to KodeKlouds courses, mainly because their labs resonate with my way of learning. My expectations were quickly proved wrong, as I found most of the topics interesting, or it brought up scenarios I already have thought about, and solved (ie. SSH key-auth). This course also made me understand AppArmor, which I had brushed off years ago as very advanced.

I spent a couple of weeks on going trough the courses and labs, before I adventured into KillerShell, where I once again was happy with my results. I scheduled and took the exam the same week as I went trough KillerShell.

While I skipped a whole task in the exam, I still managed to pass this too.

[^1]: Linux Containers is an operating-system-level virtualization method for running multiple isolated Linux systems (containers) on a control host using a single Linux kernel. [Wikipedia](https://en.wikipedia.org/wiki/LXC)
[^2]: Initiative created by Docker to define standards for multiple aspects regarding running containers. [OpenContainers](https://opencontainers.org/)
[^3]: Called Network Plugin in the [Kubernetes docs](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/), a component that handles networking between pods.
[^4]: The package manager for Kubernetes. [helm.sh](https://helm.sh/)
[^5]: Argo CD is a declarative, GitOps continuous delivery tool for Kubernetes. [argoproj.github.io](https://argoproj.github.io/)
[^6]: Software responsible for receiving the traffic from a Cloudflare tunnel. [Github](https://github.com/cloudflare/cloudflared)
