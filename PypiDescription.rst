Partial documentation mkdocs plugin and tools

Usage Scenarios:

- **Keep documentation close to the code:** When a project has multiple repositories, each with its own documentation, the documentation site can be assembled from all repository docs.
- **Share a documentation subset across multiple sites:** For projects that share some code but maintain independent documentation, the shared documentation part can be distributed as a package and linked to each project site.
- **Synchronize the look and feel of multiple sites:** When several documentation sites need a unified look and feel, the shared site configuration and UI customizations can be distributed, even though the content differs.
- **Bypass the MkDocs requirement to keep all content in the docs_dir:** If the docs_dir constraint is limiting, documentation content from outside docs_dir can be linked into the site.

`Documentation <https://docs.exordis.com/Partial%20Documentation/>`_