import frontmatter
from mkdocs import plugins
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File, Files, InclusionLevel
from mkdocs_redirects.plugin import RedirectPlugin  # pylint: disable=import-error


class RedirectPluginShim(RedirectPlugin):

    @plugins.event_priority(-100)
    def on_files(self, files, config, **kwargs):
        return super().on_files(files, config, **kwargs)

    def add_redirects(self, files: Files, file, redirect_from: list[str], config: MkDocsConfig):
        for redirect in redirect_from:
            self.config.setdefault("redirect_maps", {})[redirect] = file.src_path.replace("\\", "/")
            # Register stub page to avoid warnings about missing link targets
            stub = frontmatter.Post("Redirect")
            stub.metadata["layout"] = "redirect"
            file = File.generated(
                config=config, src_uri=redirect, content=frontmatter.dumps(stub), inclusion=InclusionLevel.EXCLUDED
            )
            files.append(file)
