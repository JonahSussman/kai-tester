import datetime
import json
import os
import sequoia_diff.actions
import sequoia_diff.loaders
import sequoia_diff.matching
import typer
import sequoia_diff
import tree_sitter
import tree_sitter_java
import yaml
import requests
import subprocess
import concurrent.futures

DEBUG = False

if DEBUG:
    import faulthandler
    import signal

    faulthandler.register(signal.SIGUSR1.value)

"""
This script is NOT production-ready at all. It has security vulnerabilities and
injection attacks abound. Please use carefully. :-)
"""


# List of Java applications and where their subsequent versions are stored
JAVA_APPLICATIONS = [
    ["fix_me_1"],
    ["io_edict_1", "io_edict_2"],
]

SERVER_URL = "http://0.0.0.0:8080"


def get_app_name(app_version: str) -> str:
    return "_".join(app_version.split("_")[:-1])


app = typer.Typer()


@app.command()
def create_application(group_id: str, artifact_id: str):
    os.chdir("versions")

    os.system(
        (
            f"mvn archetype:generate "
            f"-DgroupId={group_id} "
            f"-DartifactId={artifact_id} "
            f"-DarchetypeArtifactId=maven-archetype-quickstart "
            f"-DarchetypeVersion=1.4 "
            f"-DinteractiveMode=false"
        )
    )

    os.chdir("..")

    os.system(f"cp java.gitignore versions/{artifact_id}/.gitignore")


@app.command()
def package():
    typer.echo("Packaging Java applications")

    for app_versions in JAVA_APPLICATIONS:
        for app_version in app_versions:
            typer.echo(f"Packaging {app_version}")
            os.chdir(os.path.join("versions", app_version))
            os.system("mvn clean package")
            os.chdir(os.path.join("..", ".."))


@app.command()
def clean():
    typer.echo("Cleaning Java applications")

    for app_versions in JAVA_APPLICATIONS:
        for app_version in app_versions:
            typer.echo(f"Cleaning {app_version}")
            os.chdir(os.path.join("versions", app_version))
            os.system("mvn clean")
            os.chdir(os.path.join("..", ".."))


@app.command()
def analyze(apps: list[str] | None = None, max_concurrent_processes: int = 3):
    typer.echo("Analyzing Java applications")

    if apps is None:
        apps = []
        for x in JAVA_APPLICATIONS:
            apps.extend(x)

    def run_analysis(app):
        typer.echo(f"Analyzing {app}")
        subprocess.run(
            [
                "./kantra",
                "analyze",
                "--input",
                f"versions/{app}",
                "--output",
                f"analysis/{app}",
                "--rules",
                "blog-post-rules",
                "--skip-static-report",
                "--overwrite",
                "--enable-default-rulesets=false",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    with concurrent.futures.ThreadPoolExecutor(max_concurrent_processes) as executor:
        futures = []
        for app_versions in JAVA_APPLICATIONS:
            for app in app_versions:
                if app not in apps:
                    continue

                futures.append(executor.submit(run_analysis, app))

        for future in concurrent.futures.as_completed(futures):
            future.result()


def dictize_action(action: sequoia_diff.models.Action):
    obj: dict
    if isinstance(action, sequoia_diff.models.Insert):
        obj = {
            "kind": "insert_node",
            "node": action.node.pretty_str_self(),
            "parent": action.parent.pretty_str_self(),
            "pos": action.pos,
            "whole_subtree": action.whole_subtree,
        }
    elif isinstance(action, sequoia_diff.models.Delete):
        obj = {
            "kind": "delete_node",
            "node": action.node.pretty_str_self(),
        }
    elif isinstance(action, sequoia_diff.models.Move):
        obj = {
            "kind": "move_node",
            "node": action.node.pretty_str_self(),
            "parent": action.parent.pretty_str_self(),
            "pos": action.pos,
        }
    elif isinstance(action, sequoia_diff.models.Update):
        obj = {
            "kind": "update_node",
            "node": action.node.pretty_str_self(),
            "old_label": action.old_label,
            "new_label": action.new_label,
        }
    else:
        raise ValueError(f"Unknown action type: {type(action)}")

    return obj


@app.command()
def diff(file_a: str, file_b: str):
    parser = tree_sitter.Parser(tree_sitter.Language(tree_sitter_java.language()))

    tree_a: tree_sitter.Tree = parser.parse(open(file_a, "rb").read())
    tree_b: tree_sitter.Tree = parser.parse(open(file_b, "rb").read())

    print(
        yaml.dump(
            [
                dictize_action(action)
                for action in sequoia_diff.get_tree_diff(tree_a, tree_b)
            ]
        )
    )


@app.command()
def create_repos():
    clean()

    os.system("rm -rf repos")
    os.system("mkdir repos")

    os.chdir("repos")

    for app_versions in JAVA_APPLICATIONS:
        # app versions look like <something>_1, <something>_2. We want to remove
        # the _1, _2, etc. Note that <something> can have underscores in it.
        app_name = "_".join(app_versions[0].split("_")[:-1])

        typer.echo(f"Creating repo for {app_name}")

        os.system(f"mkdir {app_name}")
        os.chdir(app_name)
        os.system(f"git init")
        os.system(f"git commit --allow-empty -m 'Initial commit'")

        for app_version in app_versions:
            os.system(f"git checkout -b {app_version}")

            # copy the git repo to a temporary location, delete the folder, and
            # copy back the .git folder
            os.chdir("..")
            os.system(f"cp -r {app_name} tmp")
            os.system(f"rm -rf {app_name}")
            os.system(f"mkdir {app_name}")
            os.system(f"cp -r tmp/.git {app_name}")
            os.system(f"rm -rf tmp")
            os.chdir(app_name)

            # Copy the version to the repo
            os.system(f"cp -r ../../versions/{app_version}/* .")
            os.system("git add .")
            os.system(f"git commit -m 'Added {app_version}'")

            input()

        os.chdir("..")

    os.chdir("..")


@app.command()
def load_store(apps: list[str]):
    if apps is None:
        apps = [get_app_name(app_versions[0]) for app_versions in JAVA_APPLICATIONS]

    for app_versions in JAVA_APPLICATIONS:
        app_name = get_app_name(app_versions[0])
        if app_name not in apps:
            continue

        typer.echo(f"Loading {app_name}")

        for app_version in app_versions:
            typer.echo(f"Loading version {app_version}")

            os.chdir(os.path.join("repos", app_name))
            os.system(f"git checkout {app_version}")
            current_commit = os.popen("git rev-parse HEAD").read().strip()
            os.chdir(os.path.join("..", ".."))

            send_json = {
                "application": {
                    "application_name": app_name,
                    "repo_uri_origin": f"file://{os.path.abspath(os.path.join('repos', app_name))}",
                    "repo_uri_local": f"file://{os.path.abspath(os.path.join('repos', app_name))}",
                    "current_branch": app_version,
                    "current_commit": current_commit,
                    "generated_at": datetime.datetime.now().isoformat(),
                },
                "report_id": app_version,
                "report_data": yaml.safe_load(
                    open(os.path.join("analysis", app_version, "output.yaml")).read()
                ),
            }

            print(yaml.safe_dump(send_json))
            input()

            response = requests.post(
                f"{SERVER_URL}/load_analysis_report",
                json=send_json,
                headers={"Content-Type": "application/json", "Accept": "text/plain"},
                timeout=3600,
            )

            print(response)
            input()


def flatten_report(report: list[dict]):
    result: list[dict] = []

    for ruleset in report:
        ruleset_name = ruleset["name"]

        for violation_name, violation in ruleset["violations"].items():
            for incident in violation["incidents"]:
                result.append(
                    {
                        "ruleset_name": ruleset_name,
                        "violation_name": violation_name,
                        "uri": incident.get("uri", ""),
                        "message": incident.get("message", ""),
                        "code_snip": incident.get("codeSnip", ""),
                        "line_number": incident.get("lineNumber", 0) - 1,
                        "variables": incident.get("variables", {}),
                    }
                )

    return result


@app.command()
def request_fix(app_name: str, app_version: str, file_path: str):
    incidents = flatten_report(
        yaml.safe_load(
            open(os.path.join("analysis", app_version, "output.yaml")).read()
        )
    )
    print(yaml.safe_dump(incidents))
    input()

    file_contents = open(file_path).read()
    file_uri = f"file://{os.path.abspath(file_path)}"

    response = requests.post(
        f"{SERVER_URL}/get_incident_solutions_for_file",
        json={
            "file_name": file_uri,
            "file_contents": file_contents,
            "application_name": app_name,
            "incidents": incidents,
        },
        headers={"Content-Type": "application/json", "Accept": "text/plain"},
        timeout=3600,
    )

    response_json = json.loads(response.json())
    print(yaml.safe_dump(response_json))

    with open("updated_file.java", "w") as f:
        f.write(response_json["updated_file"])


if __name__ == "__main__":
    app()
