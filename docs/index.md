# Partial Documentation

Partial documentation is a framework enabling writers of [mkdocs](https://www.mkdocs.org/) based documentation to deliver parts of documentation as python packages rather than putting all documentation to single code base.

Scenarios:

- **Keep docs close to code:**  some project has multiple repositories, each repository has its documentation. Documentation site is assembled from all repositories docs
- **Share documentation subset between multiple documentation sites:** multiple projects share some code and expose documentation independently, but documentation of shared part is distributed as package and linked to all project sites 
- **Sync up look and feel of multiple documentation sites:** Multiple documentation sites have to have similar look and feel, while content differs, site config and UI customizations may be shared in this case
- **Overcome [mkdocs](https://www.mkdocs.org/) constraint to have all content in `docs_dir` directory:** For some reason constraint to have all docs in [mkdocs](https://www.mkdocs.org/) `docs_dir` directory does not work, content of directory out of  `docs_dir` may be linked to the documentation site   

## Plugins

### Docs Package

`docs_package` plugin implements takin of some directory and injecting its content to specified directory of documentation site. It may be just directory out of `docs_dir` in basic case or one may inherit from `DocsPackagePlugin` and create package serving documentation fro its resources.

#### Configuration

- `enabled` - bool allows to disable plugin from config keeping other configuration in place
- `docs_path` - path to take content files from.
- `directory` - directory of the site documentation to inject teh content to. Should be relative path to `docs_dir`. Pass empty string to inject content to the root of teh site
- `name` - name to be used to reference package . Default mkdocs assigned plugin name - plugin entrypoint name for with #N added if there are multiple instances. Eg. if `docs_package`is registered twice with config by default names would be `docs_package #1` and `docs_package #2`
- `edit_url_template` - template of edit url provided each injected page will have `edit_url` set based on this template that will show `edit` links (e.g to github or gitlab editing of original file). Must be string with `{path}` as placeholder replaced with path relative to `docs_path`. E.g for gitlab it may be `"${CI_PROJECT_URL}/-/edit/${CI_COMMIT_BRANCH}/{path}?ref_type=heads"`

#### Basic usage

To inject content of the directory out of `docs_path`

```
site_name: "Basic Usage"
plugins:
  - docs_package:
      directory: injected1
      docs_path: ~/my-docs/injected1/ # path to the directory containing files to be injected
      name: injected1
  - docs_package:
      directory: injected2
      docs_path: ~/my-docs/injected2/ # path to the directory containing files to be injected
      name: injected2
```

#### Integrations

##### Macros

If [mkdocs-macros](https://mkdocs-macros-plugin.readthedocs.io/) plugin is detected is detected `docs_package` will register `package_link` macros to construct links to the injected content:
```
[Injected page]({{'{{'}} "index.md" | package_link("injected2") {{'}}'}} )
```
with config above will generate `injected2/index.md` link


[Injected page]({{ "index.md" | package_link("injected2") }} )


##### Spellcheck

##### Mkdocs Material Blogs

### Partial Docs

## Creating Packages

### Site Package

### Docs Package

## Writing documentation 




