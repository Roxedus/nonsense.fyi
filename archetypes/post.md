---
title: "{{ replace .Name "-" " " | title }}"
date: {{ .Date }}
draft: true
tags: ["Blog"]
author: "Roxedus"
draft: true
description: "Desc Text."
canonicalURL: "{{ .Site.BaseURL }}posts/{{ replace .Name " " "-" }}"
cover:
    image: "images/cover.png"
    alt: "<alt text>"
    caption: "<text>"
---
