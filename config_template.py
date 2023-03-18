token = ''
aisearchId = ''
sync_directory = ''
article_template = '''---
article_id: {article_id}
title: {title}
description: {description}
url: {url}
created: {created}
updated: {updated}
---

> [!summary] 描述
> {description}

> [!md] Metadata
> **标题**:: {title}
> **日期**:: {created}

## Annotations

{marks}
'''
mark_template = '''> {highlight}
{tags}

{note_text}
'''