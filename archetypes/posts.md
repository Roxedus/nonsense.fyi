---
title: "{{ replace .File.ContentBaseName `-` ` ` | title }}"
date: "{{ time.Now.Format `2006-01-02` }}"
draft: true
tags: ["Blog"]
author: "Roxedus"
description: "Desc Text."
canonicalURL: "{{ .Site.BaseURL }}posts/{{ replace .Name ` ` `-` }}"
cover:
    image: "images/cover.png"
    alt: "<alt text>"
    caption: "<text>"
---
