---
title: "Templating templates with templates"
date: 2022-10-01T00:00:00+02:00
draft: true
tags: ["Automation", "Linuxserver.io"]
author: "Roxedus"
draft: false
ShowToc: true
description: "When you go too far with Jinja"
cover:
  image: "images/undraw_hacker_mind_lsio.svg"
  alt: "Person walking in front of a screen"
---

Over at Linuxserver we use Ansible for it's convenient integration with Jinja, a templating engine for Python, along with its powerful framework to execute shell commands. With this we are able to automate quite a lot of work, like generating a uniform and recognizable README, or injecting files into the container(don't worry, the files are committed and pushed to GitHub before the image is built) for some logic. In order for all this to work, most of the metadata is filled into two YAML files in each repository, `jenkins-vars.yml` and `readme-vars.yml` which are then presented to Ansible as variables used for consumption in the templates.

## Why?

Having all the metadata stored in a couple of files that can be pragmatically read makes it relatively easy to expand what we are able to output, and ensuring changes propagates trough all outputs.

Aside from the Dockerfiles, the mentioned var files, and most of the `root/` folder, the rest of the repository are actually templated. The benefit of this approach is huge, as we often only need to update a file once, and the changes are done in the repositories as they receive updates, like when we enabled and started promoting GHCR as the default registry for all our images, with a single [pull request](https://github.com/linuxserver/docker-jenkins-builder/pull/69/files).

If you are used to the(now paid) feature of DockerHub, rebuilding images when the repository updated on GitHub, one would be accustomed to the idea of the readme on DockerHub to always reflect the readme on GitHub, however that is not the case, regardless if the repositories are linked. It is traditionally a thing you have to update by hand, however with some creative thinking you can update this with code, which we do. This means that the readme on GitHub and DockerHub is always up-to-date and identical(as long as it's not to long for DockerHub). There's also a derivative from the readme published to the [documentation site](https://docs.linuxserver.io) for each image, going more in-depth for sections of the readme. To up the inception scale, we also template the CI/CD pipeline, from the small stuff like the [greetings bot](https://github.com/linuxserver/docker-jenkins-builder/blob/master/roles/generate-jenkins/templates/greetings.j2) to the whole [Jenkinsfile](https://github.com/linuxserver/docker-jenkins-builder/blob/master/roles/generate-jenkins/templates/Jenkinsfile.j2) used to build, test and push the images.

## Remembering the once-in-a-while tasks

As I touched on in the blog post [announcing automated Unraid templates](https://www.linuxserver.io/blog/automating-the-boring-stuff-with-jinja), creating templates for Unraid was a manual task, often depending on someone in the Linuxserver team using Unraid to actually creating one, this could mean it had the potential to take days or even weeks to push a template. As there is a decent amount of tasks tied to launching a image it might even be forgotten, so automating this step would be better for everyone involved.

## How?

As outlined earlier the important building-blocks are present, a templating engine and repository-level metadata, despite this I had to create some new blocks.

This adventure started with getting reacquainted to XML, as that's how the Unraid templates are stored, remembering the specification will surely help with some future headaches.

### Getting started

I start by making some helpful notes to any potential contributor wanting to help us maintaining the template, pointing them to the correct file for changing the output. As this is done in the template, the full address for the `readme-vars.yml` file will point to the actual repository.

  ```xml {linenostart=40}
  <?xml version="1.0"?>
  <!-- DO NOT CHANGE THIS FILE MANUALLY, IT IS AUTOMATICALLY GENERATED -->
  <!-- GENERATED FROM {{ project_github_asset }}/readme-vars.yml -->
  ```

#### Simple string substitution and conditionals

Now it's time to create the stuff that actually matters for Unraid, this is stored under the `Container` tag in the XML file.

  ```jinja {linenostart=43}
  <Container version="2">
    <Name>{{ param_container_name | lower }}</Name>
    <Repository>lscr.io/{{ lsio_project_name_short }}/{{ project_name }}</Repository>
    <Registry>https://github.com/orgs/{{ lsio_project_name_short }}/packages/container/package/{{ project_name }}</Registry>
    <Network>{{ param_net if param_usage_include_net is sameas true else 'bridge' }}</Network>
    <Privileged>{{ "true" if privileged is sameas true else "false" }}</Privileged>
    <Support>{{ project_github_repo_url }}/issues/new/choose</Support>
    <Shell>bash</Shell>
    <ReadMe>{{ project_github_repo_url }}{{ "#readme" }}</ReadMe>
    <Project>{{ project_url }}</Project>
    <Overview>{{ ca(project_blurb) | trim }}</Overview>
    <GitHub>{{ project_github_repo_url }}{{ "#application-setup" if app_setup_block_enabled is defined and app_setup_block_enabled }}</GitHub>
    <TemplateURL>{{ "false" if unraid_template_sync is sameas false else "https://raw.githubusercontent.com/linuxserver/templates/main/unraid/" + project_name | lower + ".xml" }}</TemplateURL>
    <Icon>https://raw.githubusercontent.com/linuxserver/docker-templates/master/linuxserver.io/img/linuxserver-ls-logo.png</Icon>
  ```

There is a few things happening here, mostly normal substituting of variables, there is also some transforming done, as `""` is not a valid value and literal booleans needed to be it's string counterpart, along with some logic to conditionally append a link. The rest of the template consists mostly of these types of substitutions and transformations. We will get to `ca()` [later](#macros-save-the-day)

#### Going in loops

Unraid templates support multiple branches. When installing from a template with multiple branches defined using Community Applications, you will get prompted with a selection box with all the branches listed in the template. {{< figure src="images/BranchPicker.png" align=center alt="Image of Unraids Branch picker" >}}
To populate these fields, I iterate from the same variable that lists the branches on the readme, however I have recently added some filtering here to avoid listing deprecated branches.

  ```jinja {linenostart=59}
  {# Set the Branches, if any Config items is overwritten. TODO: handle config items #}
  {% if development_versions is defined and development_versions == "true" %}
  {% for item in development_versions_items if not "deprecate" in item.desc.lower() %}
      <Branch>
          <Tag>{{ ca(item.tag) }}</Tag>
          <TagDescription>{{ ca(item.desc) }}</TagDescription>
  {% if item.tag != "latest" %}
          <ReadMe>{{ project_github_repo_url }}{{ "/tree/" + item.tag + "#readme" }}</ReadMe>
          <GitHub>{{ project_github_repo_url }}{{ ("/tree/" + item.tag + "#application-setup") if app_setup_block_enabled is defined and app_setup_block_enabled }}</GitHub>
  {% endif %}
  {% if item.extra is defined %} {#- Allow for branch-specific stuff #}
          {{ ca(item.extra) | indent(8) | trim }}
  {% endif %}
      </Branch>
  {% endfor %}
  {% endif %}
  {# Set the Branches, if any #}
  ```

This snippet is just a simple loop going over the `development_versions_items` list of arrays if `development_versions` exists. The following `readme-vars.yml` produced the above screenshot:

  ```yaml
  # development version
  development_versions: true
  development_versions_items:
    - { tag: "latest", desc: "Stable Radarr releases" }
    - { tag: "develop", desc: "Radarr releases from their develop branch" }
    - { tag: "nightly", desc: "Radarr releases from their nightly branch" }
    - { tag: "nightly-alpine", desc: "Radarr releases from their nightly branch using our Alpine baseimage" }
  ```

I took the opportunity to add a key called `extra` for the dictionary, as CA has the ability to have separate config variables per branch. Unfortunately this is implemented in a way which makes it hard to use, the presence of any branch-specific items disregards all other config tags specified in the `Container` tag. Meaning that a dictionary like `{ tag: "nightly", desc: "Radarr releases from their nightly branch", extra: { nightly_var: "Do monkeydance"} }` would render all other configuration items(such as environment variables, bind mounts and port mappings) void, if this branch was chosen. This is something I might have to account for at some time, by essentially generating the same values once per branch.

### Baby's first macro

The next part I wanted to tackle, was building the link for the WebUI, here I had to be creative, while the information needed was present, it is not easily accessible as it is stored in the format Groovy wants variables to be presented in a Jenkinsfile. The input would look like this for the SWAG image:

  ```yaml
  repo_vars:
    - EXT_PIP = 'certbot'
    - BUILD_VERSION_ARG = 'CERTBOT_VERSION'
    - LS_USER = 'linuxserver'
    - LS_REPO = 'docker-swag'
    - CONTAINER_NAME = 'swag'
    - DOCKERHUB_IMAGE = 'linuxserver/swag'
    - DEV_DOCKERHUB_IMAGE = 'lsiodev/swag'
    - PR_DOCKERHUB_IMAGE = 'lspipepr/swag'
    - DIST_IMAGE = 'alpine'
    - MULTIARCH='true'
    - CI='true'
    - CI_WEB='false'
    - CI_PORT='80'
    - CI_SSL='false'
    - CI_DELAY='30'
    - CI_DOCKERENV='TEST_RUN=1'
    - CI_AUTH=''
    - CI_WEBPATH=''
  ```

Getting the value of `CI_PORT` is not as easy as it should be, like using a getter on `repo_vars` does not work. Fortunately we can use some clever replacements and splits of each item under `repo_vars` to build a new and usable variable.

  ```jinja {linenostart=1}
  {#- Create a real object from repo_vars -#}
  {%- set better_vars={} -%}
  {%- for i in repo_vars -%}
  {%- set i=(i | replace(' = ', '=', 1) | replace('=', '¯\_(ツ)_/¯', 1) | replace("'", "") | replace('"', "")).split('¯\_(ツ)_/¯') -%}
  {%- set x=(better_vars.__setitem__(i[0], i[1])) -%}
  {%- endfor -%}
  ```

The new variable this creates is called `better_vars`, which is a dictionary-type. I and X is used as throwaway variables, as Jinja does not really have a good way to run straight up code(and with good reason, I imagine). Since `repo_vars` is a array-type, it serves as a iterator, and saves me from even more [bodging](https://www.youtube.com/watch?v=lIFE7h3m40U). First order of business is to make the list uniform across both ways of placing the equals-sign, after this they don´t have any padding with spaces, I can start replacing and splitting the rest of the line until it has some resemblance of a typical python-like key-value pair.

In the first iteration of this code, there was no shrug, but a carefully chosen example above highlights how the split would work against us, the macro would fail when it arrived at `CI_DOCKERENV`, as the value of that key, is a key-value pair.

We are now working in Python land, so we can remove both double and single quotes, this can come back and bite us later, but as it stands right now this is not an issue. Currently `CI_DOCKERENV='TEST_RUN=1'` would be `CI_DOCKERENV¯\_(ツ)_/¯TEST_RUN=1`, this is not useful yet, but we just need to convert this string to a key-value pair, easily done by using `¯\_(ツ)_/¯` as the deliminator. Once we have this key-value pair we can use the `__setitem__` function of the built in python [dictionary-type](https://docs.python.org/3/reference/datamodel.html#object.__setitem__).

After all that there is now a variable that's easier to work with, simply by using a getter.

  ```jinja {linenostart=82}
  {# Set the WebUI link based on the link the CI runs against #}
  {% if better_vars.get("CI_WEB") and better_vars.get("CI") == "true" %}
      <WebUI>{{ "https" if better_vars.get("CI_SSL") == "true" else "http" }}://[IP]:[PORT:{{ better_vars.get("CI_PORT") }}]</WebUI>
  {% endif %}
  ```

This value is not supposed to hold a real URL, just the parts necessary for Unraid to build one. To do this it needs to know what container port the application is running on, we do this by using the syntax `[PORT:80]`. Now, if a user maps the container port of 80 to say host port 180, the Unraid webui button would now point to the ip of Unraid with port 180.

#### Macros save the day

When we told Squid(the guy running Community Applications) to switch us over to the new repo, we actually got [blacklisted](https://github.com/Squidly271/AppFeed/commit/91fd6193070a984efdb7e264e88251a07b450fe6#diff-2ee25025f58fc6dc397dea224c5c4b2d24d1c245efba03f2b2c4035f8e20a46e) in CA because I forgot how more-than and the less-than sign got treated both by xml and CA(Community Applications) specifically. In CA they are blacklisted characters, simply having them in the user-facing parts of the template gets the whole template repository blacklisted. This prompted a new macro, one to filter out the illegal characters.

  ```jinja {linenostart=29}
  {%- macro ca(str) -%}
  {{ str | replace("<", "") | replace(">", "") | replace("[", "") | replace("]", "") | replace("&", "and") | escape }}
  {%- endmacro -%}
  ```

This macro simply replaces `<`, `>`, `[` and `]` with nothing, while turning `&` to a word. For extra safety I put the [escape](https://jinja.palletsprojects.com/en/2.11.x/templates/#escape) filter at the end. At the time of writing there is no supported syntax in CA to make a hyperlink from a word.
All "free text" input in the template goes trough this filter to prevent another blacklisting.

#### Getting warm

Now that I have gotten the taste, and gist of using macros, I made another couple of them to keep myself DRY(Don´t Repeat Yourself)

  ```jinja {linenostart=32}
  {%- macro readme_date(str) -%}
  {%- set _date = (str | replace(":","")).split(".") -%}
  {{ "20" + _date[2] + "-" + _date[1] + "-" + _date[0] }}
  {%- endmacro -%}
  {%- macro mask(str) -%}
  {{ "true" if ["token", "pass" ,"key"]|select("in", str|lower) else "false" }}
  {%- endmacro -%}
  ```

Since the schema made for CA supports showing a changelog, we might as well use it, the metadata needed is already present in `readme-vars.yml` so no real work to get the data is needed. As this is the internet, and people come from different places, the dateformat we use is of course incompatible with the one CA accept, so I made a macro to convert `mm.dd.yy` to `yyyy.mm.dd`.
Next up is a macro that gets called when creating environment variables, to determine if the variable should be masked.

Along with a entry to list potential requirements, the changelog macro is used like this:

  ```jinja {linenostart=89}
  {% if unraid_requirement is defined and unraid_requirement != "" %}
      <Requires>{{ unraid_requirement }}</Requires>
  {% endif %}
  {# Create changelog #}
  {% if changelogs is defined and changelogs %}
      <Date>{{ readme_date(changelogs |map(attribute='date') | first) }}</Date>
      <Changes>
  {% for item in changelogs %}
  ### {{ readme_date( item.date ) }}
  - {{ ca(item.desc) }}

  {% endfor %}
      </Changes>
  {% endif %}
  ```

### The long boi

Another thing you might want to do with your container is passing along some less common parameters, like memory or cpu limits. This is something I had to tackle with ""code"". As the metadata for this is more literal to the real compose way of writing it, implementing support for security options is also coming.

  ```jinja {linenostart=8}
  {#- Create ExtraParam for REQUIRED stuff-#}
  {%- set ExtraParam=[] -%}
  {%- set x=ExtraParam.append("--hostname=" + param_hostname) if param_usage_include_hostname is sameas true -%}
  {%- set x=ExtraParam.append("--mac-address=" + param_mac_address) if param_usage_include_mac_address is sameas true -%}
  {%- if cap_add_param is defined -%}
  {%- for item in cap_add_param_vars -%}
  {%- set x=ExtraParam.append("--cap-add=" + item.cap_add_var) -%}
  {%- endfor -%}
  {#- custom_params -#}
  {%- if custom_params is defined -%}
  {%- for item in custom_params -%}
  {%- if item.array is not defined -%}
  {%- set x=ExtraParam.append("--" + item.name+ "=" + item.value) -%}
  {%- else -%}
  {%- for item2 in item.value -%}
  {%- set x=ExtraParam.append("--" + item.name+ "=" + item2) -%}
  {%- endfor -%}
  {%- endif -%}
  {%- endfor -%}
  {%- endif -%}
  {%- endif -%}
  ```

This logic defines a variable called `ExtraParam`, then massages different entries from the metadata, to a array of strings, where each item in the array is a valid docker run argument.

### The normal stuff

This article is not written in a chronological order based on the development cycle, rather following the structure in the end product. You can see this by the lack of macros in the rest of the template, if I ever have to do major revisions of this template, turning this into macros would be the first thing to do.

#### Ports

A good chunk of the applications we bundle, uses multiple ports for different purposes, this is why we have sections in our metadata for optional ports. Thankfully Unraid has the ability to display if a port is optional or not. The schema also exposes the protocol part of a port mapping, a value we also have support for in our metadata. Now we you can see the CA macro in action, it is used to clean characters from our metadata.

There is a lot of logic present to build the description and name of these ports. It will automatically name the first port as "WebUI", or it will fall back to the naming Unraid would use. For the description it will use the one defined in the metadata, or fall back to the value Unraid would have used. Mostly the same logic is used in the optional ports.

  ```jinja {linenostart=103}
  {# Set required ports, gets the name from the name atribute if present, or "WebUI" if it is the first port #}
  {% if param_usage_include_ports | default(false) %}
  {% for item in param_ports %}
  {% set port, proto=item.internal_port.split('/') if "/" in item.internal_port else [item.internal_port, false] %} {#- Logic to get the protocol #}
      <Config Name="{{ ca(item.name) if item.name is defined else "WebUI" if loop.first else "Port: " + port }}" Target="{{ port }}" Default="{{ ca(item.external_port) }}" Mode="{{ proto if proto else "tcp" }}" Description="{{ ca(item.port_desc) if item.port_desc is defined else "Container Port: " + port }}" Type="Port" Display="always" Required="true" Mask="false"/>
  {% endfor %}
  {% endif %}
  {#- Set required ports, gets the name from the name atribute if present, or "WebUI" if it is the first port #}
  {#- Set optional ports #}
  {% if opt_param_usage_include_ports | default(false) %}
  {% for item in opt_param_ports %}
  {% set port, proto=item.internal_port.split('/') if "/" in item.internal_port else [item.internal_port, false] %} {#- Logic to get the protocol #}
      <Config Name="{{ ca(item.name) if item.name is defined else "Port: " + port }}" Target="{{ port }}" Default="{{ ca(item.external_port) }}" Mode="{{ proto if proto else "tcp" }}" Description="{{ ca(item.port_desc) if item.port_desc is defined else "Container Port: " + port }}" Type="Port" Display="always" Required="false" Mask="false"/>
  {% endfor %}
  {% endif %}
  {#- Set optional ports #}
  ```

#### Volumes

The logic used for volumes is pretty much a copy-paste from the ports-logic, but instead of looking "WebUI", it is trying to find a volume to call "Appdata". There is also a piece of extra logic to see if a bind-volume is marked as Read Only.

  ```jinja {linenostart=126}
  {#- Set required volumes, gets the name from the name atribute if present, or "Appdata" if it is the /config location #}
  {% if param_usage_include_vols | default(false) %}
  {% for item in param_volumes %}
  {% set path, mode=item.vol_path.split(':') if ":" in item.vol_path else [item.vol_path, false] %} {#- Logic to get the mode #}
      <Config Name="{{ ca(item.name) if item.name is defined else "Appdata" if path == "/config" else "Path: " + path }}" Target="{{ ca(path) }}" Default="{{ ca(item.vol_host_path) if item.default is defined and item.default is sameas true }}" Mode="{{ mode if mode else "rw" }}" Description="{{ ca(item.desc) if item.desc is defined else "Path: " + path }}" Type="Path" Display="{{ "advanced" if path == "/config" else "always" }}" Required="true" Mask="false"/>
  {% endfor %}
  {% endif %}
  {#- Set required volumes, gets the name from the name atribute if present, or "Appdata" if it is the /config location #}
  {#- Set optional volumes #}
  {% if opt_param_usage_include_vols | default(false) %}
  {% for item in opt_param_volumes %}
  {% set path, mode=item.vol_path.split(':') if ":" in item.vol_path else [item.vol_path, false] %} {#- Logic to get the mode #}
      <Config Name="{{ ca(item.name) if item.name is defined else "Appdata" if path == "/config" else "Path: " + path }}" Target="{{ ca(path) }}" Default="{{ ca(item.vol_host_path) if item.default is defined and item.default is sameas true }}" Mode="{{ mode if mode else "rw" }}" Description="{{ ca(item.desc) if item.desc is defined else "Path: " + path }}" Type="Path" Display="always" Required="false" Mask="false"/>
  {% endfor %}
  {% endif %}
  {#- Set optional volumes #}
  ```

#### Variables

The base of the logic for variables is also based on the ports-logic, but it does filter away some variables we hardcode, or variables that Unraid automatically manages.

The id´s for puid and guid in Unraid, is following a agreed upon id from the early days, the 99 user is ´nobody´.

  ```jinja {linenostart=135}
  {% set skip_envs=["puid", "pgid", "tz", "umask"] %} {#- Drop envs that are either hardcoded, or automaticcly added by unraid #}
  {#- Set required variables, gets the name from the name atribute #}
  {% if param_usage_include_env | default(false) %}
  {% for item in param_env_vars if not item.env_var | lower is in skip_envs %}
      <Config Name="{{ ca(item.name) if item.name is defined else item.env_var }}" Target="{{ item.env_var }}" Default="{{ item.env_options | join('|') if item.env_options is defined else ca(item.env_value) }}" Description="{{ ca(item.desc) if item.desc is defined else "Variable: " + path }}" Type="Variable" Display="always" Required="true" Mask="{{ mask(item.env_var) }}"/>
  {% endfor %}
  {% endif %}
  {#- Set required variables, gets the name from the name atribute #}
  {#- Set optional variables #}
  {% if opt_param_usage_include_env | default(false) %}
  {% for item in opt_param_env_vars if not item.env_var | lower is in skip_envs %}
      <Config Name="{{ ca(item.name) if item.name is defined else item.env_var }}" Target="{{ item.env_var }}" Default="{{ ca(item.env_value) }}" Description="{{ ca(item.desc) if item.desc is defined else "Variable: " + path }}" Type="Variable" Display="always" Required="false" Mask="{{ mask(item.env_var) }}"/>
  {% endfor %}
  {% endif %}
  {#- Set optional variables #}
      <Config Name="PUID" Target="PUID" Default="99" Description="Container Variable: PUID" Type="Variable" Display="advanced" Required="true" Mask="false"/>
      <Config Name="PGID" Target="PGID" Default="100" Description="Container Variable: PGID" Type="Variable" Display="advanced" Required="true" Mask="false"/>
      <Config Name="UMASK" Target="UMASK" Default="022" Description="Container Variable: UMASK" Type="Variable" Display="advanced" Required="false" Mask="false"/>
  ```

#### Devices

The logic for devices is also very similar, without any special treatment.

  ```jinja {linenostart=153}
  {# Set required devices, gets the name from the name atribute #}
  {% if param_device_map | default(false) %}
  {% for item in param_devices %}
      <Config Name="{{ ca(item.name) if item.name is defined else item.device_path }}" Default="{{ item.device_path }}" Description="{{ ca(item.desc) if item.desc is defined else "Device: " + path }}" Type="Device" Display="always" Required="true" Mask="false"/>
  {% endfor %}
  {% endif %}
  {#- Set required variables, gets the name from the name atribute #}
  {#- Set optional devices #}
  {% if opt_param_device_map | default(false) %}
  {% for item in opt_param_devices %}
      <Config Name="{{ ca(item.name) if item.name is defined else item.device_path }}" Default="{{ item.device_path }}" Description="{{ ca(item.desc) if item.desc is defined else "Device: " + path }}" Type="Device" Display="always" Required="false" Mask="false"/>
  {% endfor %}
  {% endif %}
  {#- Set optional devices #}
  </Container>
  ```

### Finishing up

The last step is to tie this template into the Ansible play, which I won´t cover here, as it´s not a bodge, like this template is.
