# Partial Documentation

Partial documentation is a framework enabling writers of [mkdocs](https://www.mkdocs.org/) based documentation to deliver parts of documentation as python packages rather than putting all documentation to single code base.

Scenarios:

- **Keep docs close to code:**  some project has multiple repositories, each repository has its documentation. Documentation site is assembled from all repositories docs
- **Share documentation subset between multiple documentation sites:** multiple projects share some code and expose documentation independently, but documentation of shared part is distributed as package and linked to all project sites 
- **Sync up look and feel of multiple documentation sites:** Multiple documentation sites have to have similar look and feel, while content differs, site config and UI customizations may be shared in this case
- **Overcome [mkdocs](https://www.mkdocs.org/) constraint to have all content in `docs_dir` directory:** For some reason constraint to have all docs in [mkdocs](https://www.mkdocs.org/) `docs_dir` directory does not work, content of directory out of  `docs_dir` may be linked to the documentation site   

## Plugins

### Docs Package

`docs_package` plugin implements takin of some directory and injecting its content to specified directory of documentation site. It may be just directory out of `docs_dir` in basic case or one may inherit from `DocsPackagePlugin` and create package serving documentation fro its resources. `docs_package` does not create any files on filesystem when injecting content , instead it uses mkdocs [`on_files`](https://www.mkdocs.org/dev-guide/plugins/#on_files). Only exception is [blogs](https://squidfunk.github.io/mkdocs-material/plugins/blog/) plugin from [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) (see below) 

#### Configuration

- `enabled` - bool allows to disable plugin from config keeping other configuration in place
- `docs_path` - path to take content files from.
- `directory` - directory of the site documentation to inject the content to. Should be relative path to `docs_dir`. Pass empty string to inject content to the root of the site
- `name` - name to be used to reference package . Default mkdocs assigned plugin name - plugin entrypoint name for with #N added if there are multiple instances. E.g. if `docs_package`is registered twice with config by default names would be `docs_package #1` and `docs_package #2`
- `edit_url_template` - template of edit url provided each injected page will have `edit_url` set based on this template that will show `edit` links (e.g to github or gitlab editing of original file). Must be string with `{path}` as placeholder replaced with path relative to `docs_path`. E.g for gitlab it may be `"${CI_PROJECT_URL}/-/edit/${CI_COMMIT_BRANCH}/{path}?ref_type=heads"`

#### Basic usage

To inject content of the directory out of `docs_path`

```
site_name: "Basic Usage"
plugins:
  - docs_package:
      directory: injected1
      docs_path: ~/my-docs/injected_dir1/ # path to the directory containing files to be injected
      name: injected1
  - docs_package:
      directory: injected2
      docs_path: ~/my-docs/injected_dir2/ # path to the directory containing files to be injected
      name: injected2
```

#### Integrations

##### Macros

If [mkdocs-macros](https://mkdocs-macros-plugin.readthedocs.io/) plugin is detected `docs_package` will register `package_link` macros taking package name as single argument and constructing link to the content injected by referenced package:
```
[Injected page]({{'{{'}} "getting-started/faq.md" | package_link("injected2") {{'}}'}} )
```
with config above will generate `injected_dir2/getting-started/faq.md` link

!!! Note
    [mkdocs](https://www.mkdocs.org/) recommends having only relative to `docs_dir`  URIs. With `package_link` macro changing inject directory of plugin does not require any changes in content  



##### Redirects

If [mkdocs-redirects](https://github.com/mkdocs/mkdocs-redirects) plugin is detected `docs_package` will

- handle `redirects`  tag in front matter as list of alternative URIs for the page
- each redirect would be registered with [mkdocs-redirects](https://github.com/mkdocs/mkdocs-redirects) as redirect from the specified path to current page

It is needed to handle cases where `docs_package` page referenced in other packages moves to new uri. Common practice is to build mkdocs site with `--strict` to treat warnings as errors while move of the page referenced in other packages produces warning about missing link target page missing. 

Having redirects allows to avoid complex flows and communication between package maintainers to handle page moves though keeps documentation consistent. 

Sample:
```yaml
---
title: FAQ
redirects:
  - getting-started/faq.md
  - guides/faq.md
---

```


##### Spellcheck

If [mkdocs-spellcheck](https://pawamoy.github.io/mkdocs-spellcheck/reference/mkdocs_spellcheck/) plugin is detected `docs_package` will 

- add each line in `known_words.txt` (if found) from injected folder to dictionary
- disable spellcheck for pages with `spellcheck: false` in front matter of the page
- disable spellcheck for parts of the page after `<!-- spellcheck: disable -->` and up to `<!-- spellcheck: enable -->` or to the end of the page content if it is missing 

##### Mkdocs Material Blogs

If [blogs](https://squidfunk.github.io/mkdocs-material/plugins/blog/) plugin from [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)  is detected `docs_package` will inject blog posts from directory having path matching `post_dir` of [blogs](https://squidfunk.github.io/mkdocs-material/plugins/blog/) plugin within injected directory (by default - `blog/posts`)


!!! note

    [blogs](https://squidfunk.github.io/mkdocs-material/plugins/blog/) plugin manipulates with filesystem, so to inject blog posts `docs_package` creates `partial` directory in `post_dir` and creates files there. It is recommended to add `[post_dir]/partial` to `.gitignore`

### Partial Docs

`partial_docs` plugin is used to load all installed plugins that inherit from `docs_package` (`docs_package` itself is not loaded). It is intended for scenario where multiple `docs_package` plugins are discovered and installed to site with CICD so that adding new package does not require mkdocs config change and it is automatically added to the site once published

#### Configuration

- `enabled` - bool allows to disable plugin from config keeping other configuration in place
- `packages` - dictionary. Key is `doc_package` inherited plugin name, value is config override

## Creating Packages

### Docs Package

Docs package may be created from directory with `mkdocs-partial package` CLI command:

```
usage: mkdocs-partial package [-h] [--source-dir SOURCE_DIR] [--package-name PACKAGE_NAME] --package-version PACKAGE_VERSION [--package-description PACKAGE_DESCRIPTION] [--output-dir OUTPUT_DIR] [--exclude EXCLUDE] [--freeze] [--directory DIRECTORY] [--title TITLE] [--edit-url-template EDIT_URL_TEMPLATE]

options:
  -h, --help            show this help message and exit
  --source-dir SOURCE_DIR
                        Directory to be packaged. Default - current directory
  --package-name PACKAGE_NAME
                        Name of the package to build. Default - normalized `--directory` value directory name.
  --package-version PACKAGE_VERSION
                        Version of the package to build
  --package-description PACKAGE_DESCRIPTION
                        Description of the package to build
  --output-dir OUTPUT_DIR
                        Directory to write generated package file. Default - `--source-dir` value directory name.
  --exclude EXCLUDE     Exclude glob (should be relative to directory provided with `--source-dir`
  --freeze              Pin doc package versions in requirements.txt to currently installed. (if there is no requirements.txt in `--source-dir` directory, has no effect)
  --directory DIRECTORY
                        Path in target documentation to inject documentation, relative to mkdocs `doc_dir`. Pass empty string to inject files directly to mkdocs `docs_dir`Default - `--source-dir` value directory name
  --title TITLE         Override title if defined in package root index.md
  --edit-url-template EDIT_URL_TEMPLATE
                        f-string template for page edit url with {path} as placeholder for markdown file path relative to directory from --docs-dir

```

A result of executing this command is wheel python package containing 

- all the content of directory set with `--source-dir` as resources
- plugin inheriting from `DocsPackagePluginConfig` with default for `directory` config option set to value provided with `--directory`
- entry point for [mkdocs](https://www.mkdocs.org/) plugin discovery with name matching `--package-name`
  
#### Sample 

```
mkdocs-partial package  --package-name my-docs-package --package-version 0.1.0 --source-dir ".\docs" --output-dir ~/packages --directory my-docs
```

will create package `~/packages/my_docs_package-0.1.0-py3-none-any.whl` with package named `my-docs-package` that may be added to mkdocs config with 

```
site_name: "Docs Package Demo"
plugins:
  - my-docs-package
```

and inject content to `/my-docs` of the site (unless overridden within `mkdocs.yml`)
  

If packaged directory contains `requirements.txt`, built package will have dependencies it defines.

### Site Package

Site package is package with mkdocs config and overrides that is to be shared or accumulate all docs packages for deployment.

It may be built with `mkdocs-partial site-package` CLI command

```
usage: mkdocs-partial site-package [-h] [--source-dir SOURCE_DIR] [--package-name PACKAGE_NAME] --package-version PACKAGE_VERSION [--package-description PACKAGE_DESCRIPTION] [--output-dir OUTPUT_DIR] [--exclude EXCLUDE] [--freeze]

options:
  -h, --help            show this help message and exit
  --source-dir SOURCE_DIR
                        Directory to be packaged. Default - current directory
  --package-name PACKAGE_NAME
                        Name of the package to build. Default - `--source-dir` value directory name.
  --package-version PACKAGE_VERSION
                        Version of the package to build
  --package-description PACKAGE_DESCRIPTION
                        Description of the package to build
  --output-dir OUTPUT_DIR
                        Directory to write generated package file. Default - `--source-dir` value directory name.
  --exclude EXCLUDE     Exclude glob (should be relative to directory provided with `--source-dir`
  --freeze              Pin doc package versions in requirements.txt to currently installed. (if there is no requirements.txt in `--source-dir` directory, has no effect)
```

built package:
- contains all the content of directory set with `--source-dir` as resources
- has dependencies from `requirements.txt`
- has CLI entry point with name matching `--package-name` that may be used to launch mkdocs 
  
#### Site Package CLI 

##### serve

launches `mkdocs serve` with option to specify:
- override for any installed docs package resource dir e.g. `--local-docs my-docs-package=./docs` will instruct my-docs-package package to inject files from `./docs` rather than from its resources
- override site root directory e.g. `--site-root ./site` will instruct site package to take mkdocs configuration and overrides from `./site` rather than from its resources

Both overrides are helpful when writing docs - site package may be installed together with all docs packages it has and lunched pointing one of the docs package to directory where package git repo is pulled locally. Thus while editing docs result will be immediately available on https://127.0.0.1:8000 in context of the full site.  Same for site with `--site-root` , configuration may be changed locally while seeing in real time how it affects the site with all docs packages installed

```
usage: [package-name] serve [-h] [--local-docs LOCAL_DOCS] [--site-root SITE_ROOT]

options:
  -h, --help            show this help message and exit
  --local-docs LOCAL_DOCS
  --site-root SITE_ROOT
```

All common args for mkdocs serve may be passed as well e.g. port and address to serve on may be changed with  `--dev-addr`, `--strict` may be passed to fail on any warning etc

##### build

launches `mkdocs build` with same overrides available  as for `serve`

```
usage: [package-name] build [-h] [--local-docs LOCAL_DOCS] [--site-root SITE_ROOT]

options:
  -h, --help            show this help message and exit
  --local-docs LOCAL_DOCS
  --site-root SITE_ROOT
```

##### dump

Dumps content of the site resources to specified directory.  E.g. it may be dumped to `~/site` , then site may be launched with `serve --site-root ~/site`  to test some changes to site configuration

```
usage: [package-name] dump [-h] [--output OUTPUT]

options:
  -h, --help       show this help message and exit
  --output OUTPUT  Output directory. Default - Current directory
```


## Real World Use Cases

Let's say you need to maintain documentation of the company developing two products. Set up of repositories on gitlab or github  may be the following in this case

- `site-company-documentation` 
    - holds `mkdocs.yml` and `requirements.txt` listing all docs packages (in advanced scenario `requirements.txt` is generated during CI with iterating all repositories with gitlab/github API ). 
    - has `partial_docs` plugin loaded with `mkdocs.yml` to automatically load all documentation packages
    - CI builds this repos with `mkdocs-partial site-package`, installs built package and publishes results of `site-company-documentation build` 
- `docs-company-documentation` 
    - Holds documentation related to company context - home page of the site, contacts etc. 
    - Docs package is referenced in `requirements.txt` of `site-company-documentation` without version constraint to grab the latest.  
    - CI builds this repository with `mkdocs-partial package --directory ""` to inject docs to the root of the site
    - CI publishes docs package to company pypi registry and triggers `site-company-documentation` rebuild 
- `product-a` 
    - holds code for product A and has `docs` directory with documentation. 
    - CI builds product and documentation for it with `mkdocs-partial package --package-name docs-project-a --directory ProdcutA` (docs are injected to directory `ProdcutA` of the site)
    - `docs-project-a` package is referenced in `requirements.txt` of `site-company-documentation` without version constraint to grab the latest. 
    - CI publishes `docs-project-a` package to company pypi registry and triggers `site-company-documentation` rebuild 
- `product-b` 
    - holds code for product A and has `docs` directory with documentation. 
    - CI builds product and documentation for it with `mkdocs-partial package --package-name docs-project-b --directory ProdcutB` (docs are injected to directory `ProdcutB` of the site)
    - `docs-project-b` package is referenced in `requirements.txt` of `site-company-documentation` without version constraint to grab the latest. 
    - CI publishes `docs-project-b` package to company pypi registry and triggers `site-company-documentation` rebuild 

!!! Note
    Injecting only release versions of packages to the site, verification of documentation with `--strict` and similar aspects are skipped for clarity

As result: 

- Site config is segregated from documentation and may have different maintainer 
- Update of any documentation package updates site 
- Each documentation package has its own maintainer
- Products documentation is updated together with the code
- Maintainers of documentation packages may write documentation seeing how it works in context of full company documentation


For example maintainer of ProductA documentation may do the following to start editing documentation 

  ```
  # Clone ProductA repository
  git clone [repo with ProductA]
  # Create and activate virtual environment 
  python3 -m pip install virtualenv
  python3 -m venv env
  source env/bin/activate
  # Install latest version of company documentation site
  python3 -m pip install site-company-documentation
  # Launch it with `docs-project-a` package taking content from local folder
  site-company-documentation serve --local-docs docs-project-a=./docs
  ```

it will start serving company documentation site on http://127.0.0.0:8000 with content for ProductA taken from local folder `./docs` . 



!!! tip
    `site-company-documentation` CI may have additional step to build docker image from site, it would make things even simpler for documentation writer as all she'd need is launching docker with something like 
    ```
    docker run --pull always --rm \
               -p 8000:8000 \
               -v .\docs:/docs \
               [docker image] serve --local-docs docs-project-a=./docs
    ```





