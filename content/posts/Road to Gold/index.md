---
title: "Road to Gold"
date: 2025-07-28T00:00:00+02:00
draft: false
tags: ["Kubernetes", "Kubestronaut", "Certification"]
author: "Simen Røstvik"
ShowToc: true
description: "My road to Golden Kubestronaut"
cover:
  image: "images/astronaut.svg"
  alt: "An astronaut holding a flag"
  source: https://undraw.co/
---

## Golden Kubestronaut

Golden Kubestronaut is a title given to active holders of all CNCF certifications, plus the Linux Foundations Certified System Administrator. At the time of writing this is a total of 14 certifications, with another one joining the ranks mid-October. This is a level up from the Kubestronaut title, which is just the Kubernetes focused certifications, the goal of the level up is to show knowledge across the larger [Cloud Native Landscape](https://landscape.cncf.io/). This post is not meant to be a sales-pitch for the programme, [CNCF's own page](https://www.cncf.io/training/kubestronaut/) does that quite well, but I do get a backpack for obtaining this title.

## How

For my journey, the most challenging part was obtaining the Kubestronaut title, as it holds 3 of 5 hands-on certifications, I covered these in a [previous post](/posts/road-to-ckad/).

This road also consists of a large number of KodeKloud courses. I like these because they also have mock exams which give some feedback on readiness for the proper exam.

### Training materials

#### GitOps Certified Associate

This certificate came before both Golden Kubestronaut and Kubestronaut had been solidified and launched.
One of my colleagues, Roberth, was involved in making this, and urged coworkers to take it. I took it the weekend it got announced, and became available to schedule. As this certificate is conceptual, and not tied to a product there is no relevant course for it. To prepare, I read the [OpenGitOps](https://opengitops.dev/) page, however most of my knowledge for this was gained by attending talks Roberth had done, like the one on [DevopsDays Oslo 2021](https://www.youtube.com/watch?v=F2Kq7fzwkdc) as well as this [webinar](https://www.youtube.com/watch?v=h-sPgvvFyKk)

#### Cilium Certified Associate

This one I had on my todo for a while, as Cilium is a project I had already worked a bit with, and wanted to learn more about, regardless of the title. Aside from having used Cilium previously, I used Isovalents [learning paths](https://isovalent.com/learning-tracks/) to discover more of Cilium. I mainly focused on the Platform Engineer and Platform Ops tracks.

#### Linux Foundation Certified System Administrator

This was the certification I spent the most time on, even though I have used Linux for at least 10 years at this point. This is a hands-on certification, so additional preparation was needed. The KodeKloud course of this is quite long, with 12 hours of video, and multiple labs for each section. The reason for me spending lots of time here, is because the course and curriculum for the certificate outlines tools that's behind wizards or helper programs in today's distros. Networking and Netplan is one of these examples, as it removes the need to manually interact with the network manager. I became somewhat frustrated doing this course, because I knew of the concepts it teaches, but not necessarily the tools. This lead me to talk to a colleague that recently took the exam, and we figured I should just do an attempt. I was not confident that I would pass this, I did however pass it with 6 points.

#### Kyverno Certified Associate

As working in restricted environments is a very real possibility, looking at Kyverno was an obvious choice. Restricting actions with a policy engine is something we already do for customers, being Kyverno or OpenPolicy Agent. KodeKloud doesn't have a course for the certificate, but they do have a hands-on course, "Learn By Doing: Kubernetes Policies with Kyverno". Along with that lab and reading the documentation for concepts I felt the lab didn't fully answer, was what I needed to feel confident enough to schedule the exam.

#### Prometheus Certified Associate

Prometheus is also something I have some experience with running. The KodeKloud course covered what I knew, and what I missed, so running through the course and scheduling the exam was no big deal.


#### Istio Certified Associate

This is the 5th, and last hands-on certification on the Golden Kubestronaut and Kubestronaut list. This is also the first one where I didn't feel comfortable to schedule after going through the KodeKloud course, I did however schedule it. This was my first failed attempt on this road. I had a lot of computer problems this day, which I probably could blame it all on. However there were several tasks I wasn't comfortable with having completed, so it really was a blessing in disguise.

With an attempt under my belt, I took a whole week reading up on Istio in the quiet times at work. While KodeKloud made a big deal of getting to know the documentation, getting to know it even further certainly wasn't in vain. I also had a better idea of what the exam focused on, in terms of details.

#### OpenTelemetry Certified Associate

This is another concept based one, and somewhat recent, so I didn't expect there to be a KodeKloud course. Linux Foundation has a starter course for OTEL, LFS148. Paired with [mock exams on Udemy](https://www.udemy.com/course/opentelemetry-certified-associate-otca-prep-practice-exams), made by a colleague, I was ready.


#### Certified Backstage Associate

Backstage as an idea for a platform portal is something that has always intrigued me, but I've always been put off because it is a framework, and thus need additional development to achieve its full potential. Linux Foundation has a free intro course to Backstage, LFS142, it is a decent introduction, good enough to understand the level of development one would have to do. It is just that, an intro, so I took the KodeKloud course as well. The course has you installing node, and other tools you need to develop against the framework, having delved in programming is a plus with this one, even better if that is with JavaScript.

#### Certified Argo Project Associate

When I first started using Kubernetes I used ArgoCD (this cluster died on me like 4 times before I set Kubernetes and Argo on pause), I've since shifted to FluxCD, so conceptually this shouldn't be a problem. KodeKloud does have a Argo course, but not for the exam, this course seemed to also cover a lot of GitOps, which I didn't feel the need to look more into, with passing CGOA and CNPA. I found this [study guide](https://github.com/Al-HusseinHameedJasim/certified-argo-project-associate), after looking at, and discarding mock exams on Udemy.

#### Cloud Native Platform Engineering Associate

This one is currently not needed for Golden, but it will be the 15th October. I got invited to take the beta exam, for which I prepared by reading the [whitepaper](https://tag-app-delivery.cncf.io/whitepapers/platforms/) for platform engineering, this is also one of Roberth's passions, so I've been disusing these concepts for a while. He has also [talked](https://www.youtube.com/watch?v=ltrbhK56OIY) about this, including on [KubeCon.](https://www.youtube.com/watch?v=iu3yWKLaY-c).

## Lot's of certifications

This is a lot of certifications, with most of them taken over a span of 4 months. I would not have gone on this road if it weren't for my employer Sopra Steria, letting me take time to do this, as well as covering the cost. Big thanks to them.

### Keeping things up to date

In addition to this rambling site, I also have a website for my portfolio on [roxedus.dev](https://roxedus.dev/). This page has a section to list certifications and other accomplishments. This section has been ignored for the last 5 or so months, so I quite recently automated this section. I did this in true cloud engineer fashion, by using curl, bash and yq. This reads the public json endpoints for my profiles on Credly and Microsoft Learn, and builds the YAML file the static site generator uses to generate this section. [This](https://github.com/Roxedus/Roxedus/blob/main/site/.get-certs.sh) is run on each GitHub Action run, meaning I only have to trigger the build with a webhook, rather than doing a git commit.