# Partial Documentation

Partial documentation is a framework that allows writers of [MkDocs](https://www.mkdocs.org/)-based documentation to deliver parts of documentation as Python packages, rather than placing all documentation in a single codebase.

Scenarios:

- **Keep documentation close to the code:** When a project has multiple repositories, each with its own documentation, the documentation site can be assembled from all repository docs.
- **Share a documentation subset across multiple sites:** For projects that share some code but maintain independent documentation, the shared documentation part can be distributed as a package and linked to each project site.
- **Synchronize the look and feel of multiple sites:** When several documentation sites need a unified look and feel, the shared site configuration and UI customizations can be distributed, even though the content differs.
- **Bypass the [MkDocs](https://www.mkdocs.org/) requirement to keep all content in the `docs_dir`:** If the `docs_dir` constraint is limiting, documentation content from outside `docs_dir` can be linked into the site.

## Installation

### PyPI 

To install `mkdocs-partial` package, run the following command from the command line:
```bash
pip install mkdocs-partial
```
This package registers the `mkdocs-partial` command through a console script entry point and includes the [MkDocs](https://www.mkdocs.org/) plugins described below.


[pypi.org project page](https://pypi.org/project/mkdocs-partial/)

### Docker 

Pull:

```bash
docker pull exordis/mkdocs-partial
```

Execute:
```bash
docker run exordis/mkdocs-partial
```

Entrypoint is mkdocs-partial. See [Creating Packages](#creating-packages) for args documentation 


[DockerHub repository](https://hub.docker.com/repository/docker/exordis/mkdocs-partial)


### GitHub

=== "Specific version"

    ```bash
    pip install git+https://github.com/exordis/mkdocs-partial@1.9.1
    ```

=== "Latest"

    ```bash
    pip install git+https://github.com/exordis/mkdocs-partial@master
    ```

[GitHub project](https://github.com/exordis/mkdocs-partial)

## Plugins

- **`docs_package`** - Injects content from a specified directory into the MkDocs documentation site.
- **`partial_docs`** - Automatically loads all installed plugins that inherit from `docs_package` for CI/CD scenarios.  

### Docs Package

The `docs_package` plugin takes the contents of a specified directory and injects them into a target directory on the documentation site. There are two main options for content injection:

- **Target directory injection**: takes the contents of a specified directory and injects them into a target directory within `docs_dir`.
  
- **Inheritance-based extension**: users can inherit from `DocsPackagePlugin` to create a package that serves documentation for specific resources.

When injecting content the `docs_package` plugin does not create any files directly on the filesystem; instead, it uses MkDocs' [`on_files`](https://www.mkdocs.org/dev-guide/plugins/#on_files) event to manage content injection. Only exception is [blogs](https://squidfunk.github.io/mkdocs-material/plugins/blog/) plugin from [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) (see below) 

#### Configuration

- `enabled` - boolean setting that allows the plugin to be disabled while keeping the rest of the configuration intact.
- `docs_path` - path specifying the location of content files to be included.
- `directory` - directory of the site documentation to inject the content to. Should be relative path to `docs_dir`. Use  empty string to inject content to the root of the site.
- `name` - name used to reference the package. By default, MkDocs assigns the plugin's entry point name, with #N added if there are multiple instances. For example if `docs_package` is registered twice, the default names would be `docs_package #1` and `docs_package #2`.
- `edit_url_template` - template for the edit URL. Each injected page will have an `edit_url` based on this template, which can be used to show `edit` links (e.g., for editing the original file on GitHub or GitLab). This must be a string with `{path}` as a placeholder, replaced by the path relative to `docs_path`.  
For example, in GitLab, it could be `"${CI_PROJECT_URL}/-/edit/${CI_COMMIT_BRANCH}/{path}?ref_type=heads"`.

#### Basic usage

To inject the content from directories outside of `docs_path`, following configuration can be used:

```yaml
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
```jinja
[Injected page]({{'{{'}} "getting-started/faq.md" | package_link("injected2") {{'}}'}} )
```
with config above will generate `injected_dir2/getting-started/faq.md` link

If package name argument is not passed to the macros, for pages managed with `docs_package` plugin it will package of the page, for other pages it will fails:
```jinja
[Injected page from the same package]({{'{{'}} "getting-started/faq.md" | package_link {{'}}'}} )
```

!!! Note
    [mkdocs](https://www.mkdocs.org/) recommends having only relative to `docs_dir`  URIs. With `package_link` macro changing inject directory of plugin does not require any changes in content  

##### Redirects

If [mkdocs-redirects](https://github.com/mkdocs/mkdocs-redirects) plugin is detected `docs_package` will

- handle `redirects`  tag in front matter as list of alternative URIs for the page
- each redirect would be registered with [mkdocs-redirects](https://github.com/mkdocs/mkdocs-redirects) as redirect from the specified path (must be relative to package directory) to current page

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

- Add each line from `known_words.txt` (if found) from injected folder to spellcheck dictionary.
- Disable spellcheck for pages that have `spellcheck: false` set in front matter.
- Disable spellcheck for for sections of a page following `<!-- spellcheck: disable -->` until  `<!-- spellcheck: enable -->` or the end of the page if `enable` is missing.
- Include `docs_package` plugin name to spellcheck warnings.

##### Mkdocs Material Blogs

If [blogs](https://squidfunk.github.io/mkdocs-material/plugins/blog/) plugin from [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)  is detected `docs_package` will inject blog posts from directory having path matching `post_dir` of [blogs](https://squidfunk.github.io/mkdocs-material/plugins/blog/) plugin within injected directory (by default - `blog/posts`)


!!! note

    [blogs](https://squidfunk.github.io/mkdocs-material/plugins/blog/) plugin manipulates with filesystem, so to inject blog posts `docs_package` creates `partial` directory in `post_dir` and creates files there. It is recommended to add `[post_dir]/partial` to `.gitignore`

### Partial Docs

`partial_docs` plugin is used to load all installed plugins that inherit from `docs_package` (excluding `docs_package` itself). It is designed for scenarios where multiple `docs_package` plugins are discovered and installed in a site with CI/CD. This allows new documentation packages to be automatically added to the site upon publishing, without requiring changes to the MkDocs configuration.

#### Configuration

- `enabled` - boolean setting that allows the plugin to be disabled while keeping the rest of the configuration intact.
- `packages` - dictionary where the key is the name of the plugin that inherits from `docs_package`, and the value is the configuration override for that plugin.

## Creating Packages

### Docs Package

Docs package may be created from directory with `mkdocs-partial package` CLI command:

```
usage: mkdocs-partial package [-h] [--source-dir SOURCE_DIR]
                              [--package-name PACKAGE_NAME] --package-version
                              PACKAGE_VERSION
                              [--package-description PACKAGE_DESCRIPTION]
                              [--output-dir OUTPUT_DIR] [--exclude EXCLUDE]
                              [--freeze] [--directory DIRECTORY]
                              [--title TITLE]
                              [--blog-categories BLOG_CATEGORIES]
                              [--edit-url-template EDIT_URL_TEMPLATE]

options:
  -h, --help            show this help message and exit
  --source-dir SOURCE_DIR
                        Directory to be packaged. Default - current directory
  --package-name PACKAGE_NAME
                        Name of the package to build. Default - normalized
                        `--directory` value directory name.
  --package-version PACKAGE_VERSION
                        Version of the package to build
  --package-description PACKAGE_DESCRIPTION
                        Description of the package to build
  --output-dir OUTPUT_DIR
                        Directory to write generated package file. Default -
                        `--source-dir` value directory name.
  --exclude EXCLUDE     Exclude glob (should be relative to directory provided
                        with `--source-dir`
  --freeze              Pin doc package versions in requirements.txt to
                        currently installed. (if there is no requirements.txt
                        in `--source-dir` directory, has no effect)
  --directory DIRECTORY
                        Path in target documentation to inject documentation,
                        relative to mkdocs `doc_dir`. Pass empty string to
                        inject files directly to mkdocs `docs_dir`Default -
                        `--source-dir` value directory name
  --title TITLE         Override title if defined in package root index.md
  --blog-categories BLOG_CATEGORIES
                        `/` separated list of categories to be prepended to
                        defined in blog posts of the package. Empty by default
  --edit-url-template EDIT_URL_TEMPLATE
                        f-string template for page edit url with {path} as
                        placeholder for markdown file path relative to
                        directory from --docs-dir
```

The result of executing this command is a Python wheel package that contains:

- All the content from the directory specified by the `--source-dir` option, included as resources.
- A plugin that inherits from `DocsPackagePluginConfig`, with the default value for the `directory` configuration option set to the value provided by `--directory`.
- An entry point for [MkDocs](https://www.mkdocs.org/) plugin discovery, with a name matching the `--package-name` option.


#### Sample 

=== "python console script"

    ```bash
    mkdocs-partial package --package-name my-docs-package --package-version 0.1.0 --source-dir ".\docs" --output-dir ~/packages --directory my-docs
    ```

=== "docker"

    ```bash
    docker run -v ./docs:/docs -v .:/packages  exordis/mkdocs-partial package --package-name my-docs-package --package-version 0.1.0 --output-dir /packages --directory my-docs
    ```


will create package `~/packages/my_docs_package-0.1.0-py3-none-any.whl` with package named `my-docs-package` that may be added to mkdocs config with 


```yaml
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
usage: mkdocs-partial site-package [-h] [--source-dir SOURCE_DIR]
                                   [--package-name PACKAGE_NAME]
                                   --package-version PACKAGE_VERSION
                                   [--package-description PACKAGE_DESCRIPTION]
                                   [--output-dir OUTPUT_DIR]
                                   [--exclude EXCLUDE] [--freeze]

options:
  -h, --help            show this help message and exit
  --source-dir SOURCE_DIR
                        Directory to be packaged. Default - current directory
  --package-name PACKAGE_NAME
                        Name of the package to build. Default - `--source-dir`
                        value directory name.
  --package-version PACKAGE_VERSION
                        Version of the package to build
  --package-description PACKAGE_DESCRIPTION
                        Description of the package to build
  --output-dir OUTPUT_DIR
                        Directory to write generated package file. Default -
                        `--source-dir` value directory name.
  --exclude EXCLUDE     Exclude glob (should be relative to directory provided
                        with `--source-dir`
  --freeze              Pin doc package versions in requirements.txt to
                        currently installed. (if there is no requirements.txt
                        in `--source-dir` directory, has no effect)
```

The built package will:

- Include all content from the directory specified by `--source-dir` as resources.
- Include dependencies listed in `requirements.txt`.
- Provide a CLI entry point named after `--package-name`, which can be used to launch MkDocs.

#### Site Package CLI 

##### Serve Documentation Locally

The `serve` command launches `mkdocs serve` with options to specify:

- **Override for any installed docs package resource directory**:  
    The option `--local-docs my-docs-package=./my-package/docs::my-package` instructs the `my-docs-package` to inject files from `./my-package/docs` instead of its default resources and use `my-package` as inject site directory instead of the one configured for plugin.
  
    Parts for docs path and directory are optional:
 
    `--local-docs my-docs-package=./my-package/docs` will keep configured directory.
 
    `--local-docs my-docs-package` will inject files from `/docs` path keep configured directory.   

- **Inject path which does not have plugin configuration in site resources**
    If plugin referenced by  `--local-docs` is not configures, configuration with provided path (fallback to `/docs`) and directory (fallback to root of the site) will be created
  
- **Override the site root directory**:  
    The option `--site-root ./site` directs the site package to load the MkDocs configuration and overrides from `./site` rather than its default resources.

These overrides are particularly useful for documentation editing. When the site package is installed with all its associated docs packages, one of the docs packages can be pointed to a local directory, such as a Git repository, allowing real-time editing. As documentation changes are made, the results are immediately available at `https://127.0.0.1:8000` in the full site context. Similarly, with the `--site-root` option, the site configuration can be adjusted locally to observe its effects on the site in real time with all docs packages installed.

```
usage: [package-name] serve [-h] [--local-docs LOCAL_DOCS] [--site-root SITE_ROOT]

options:
  -h, --help            show this help message and exit
  --local-docs LOCAL_DOCS
                        loads local directory as `docs_package` plugin content. Format <plugin name>[=<docs_path>[::<directory>]]. If `docs_path` is not provided `/docs` is
                        used as default. If plugin is configured within site mkdocs.yml `directory` overrides corresponding plugin config option. If plugin not configured
                        within site mkdocs.yml, it is added to config
  --site-root SITE_ROOT
                        loads local directory as site `docs_dir` instead of the content packed with site package
```

All standard arguments for `mkdocs serve` can be passed as well. For example, the server’s port and address can be changed using `--dev-addr`, and `--strict` can be used to trigger a failure on any warning.

##### Build Static Documentation

The `build` command launches `mkdocs build`, with the same overrides available as for the `serve` command.

```
usage: [package-name] build [-h] [--local-docs LOCAL_DOCS] [--site-root SITE_ROOT]

options:
  -h, --help            show this help message and exit
  --local-docs LOCAL_DOCS
                        loads local directory as `docs_package` plugin content. Format <plugin name>[=<docs_path>[::<directory>]]. If `docs_path` is not provided `/docs` is
                        used as default. If plugin is configured within site mkdocs.yml `directory` overrides corresponding plugin config option. If plugin not configured
                        within site mkdocs.yml, it is added to config
  --site-root SITE_ROOT
                        loads local directory as site `docs_dir` instead of the content packed with site package

```

##### Export Site Resources

The `dump` command exports the site's resources to a specified directory. For example, the content can be dumped to `~/site`, and the site can then be served using `serve --site-root ~/site` to test configuration changes locally.

```
usage: [package-name] dump [-h] [--output OUTPUT]

options:
  -h, --help       show this help message and exit
  --output OUTPUT  Output directory. Default - Current directory
```

## Real World Use Cases

Consider a scenario where an organization needs to maintain the documentation for two products. The setup for repositories on GitLab or GitHub might look like this:

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

As a result:

- The site configuration is separated from the documentation and can have a different maintainer.
- Updating any documentation package will automatically update the site.
- Each documentation package has its own maintainer.
- Product documentation is updated alongside the code, ensuring consistency.
- Documentation package maintainers can write and test documentation in the context of the full company site.


For example maintainer of ProductA documentation may do the following to start editing documentation 

  ```bash
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
    ```bash
    docker run --pull always --rm \
               -p 8000:8000 \
               -v ./docs:/docs \
               [docker image] serve --local-docs docs-project-a=./docs
    ```
