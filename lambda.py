import os
import re
import boto3
import logging

# configure logging
logging.getLogger().setLevel(logging.INFO)

# init globals
ENV_TAG = "dev"
if "IMAGE_TAG" in os.environ:
    ENV_TAG = os.environ["IMAGE_TAG"]
DISABLE_OLD_ECS = "on"
if "DISABLE_OLD_ECS" in os.environ:
    DISABLE_OLD_ECS = os.environ["DISABLE_OLD_ECS"]
UPDATE_ECS = "off"
if "UPDATE_ECS" in os.environ:
    UPDATE_ECS = os.environ["UPDATE_ECS"]
UPDATE_LAMBDA = "off"
if "UPDATE_LAMBDA" in os.environ:
    UPDATE_LAMBDA = os.environ["UPDATE_LAMBDA"]

# init boto3 clients
ECS = boto3.client("ecs")
LDA = boto3.client("lambda")


def handler(event, context):
    logging.info(f"ENV_TAG:{ENV_TAG}")

    # check event
    if (
        "detail" in event
        and "repository-name" in event["detail"]
        and "image-digest" in event["detail"]
        and "image-tag" in event["detail"]
    ):
        # check image tag
        logging.info(f"EVT_TAG:{event['detail']['image-tag']}")
        if ENV_TAG == event["detail"]["image-tag"]:
            # log event data
            logging.info(f"EVT_REPO:{event['detail']['repository-name']}")
            logging.info(f"EVT_DIGEST:{event['detail']['image-digest']}")

            # browse lambda functions
            if UPDATE_LAMBDA == "on":
                paginator = LDA.get_paginator("list_functions")
                iterator = paginator.paginate()
                for page in iterator:
                    logging.info("Browsing lambda functions...")
                    for f in page["Functions"]:
                        if f["PackageType"] == "Image":
                            logging.info(f"FUNCTION_NAME:{f['FunctionName']}")
                            process_function(
                                f["FunctionArn"],
                                event["detail"]["repository-name"],
                                event["detail"]["image-digest"],
                            )

            # browse ecs task definitions
            if UPDATE_ECS == "on":
                families = []
                previous_family = ""
                paginator = ECS.get_paginator("list_task_definitions")
                iterator = paginator.paginate(status="ACTIVE", sort="DESC")
                for page in iterator:
                    logging.info("Browsing ecs task definitions...")
                    for arn in page["taskDefinitionArns"]:
                        s = arn.split(":")
                        family = s[5][16:]
                        logging.info(f"FAMILY:{family}")
                        if family != previous_family:
                            previous_family = family
                            if process_task_definition(
                                arn,
                                event["detail"]["repository-name"],
                                event["detail"]["image-digest"],
                            ):
                                families.append(family)
                        elif DISABLE_OLD_ECS == "on":
                            logging.info(f"...DEREGISTERING:{s[6]}")
                            ECS.deregister_task_definition(taskDefinition=arn)

                # rolling update ecs services
                if len(families) > 0:
                    update_services(families)

        else:
            logging.warning("Invalid Image Tag!")

    else:
        logging.warning("Invalid Event!")

    # the end
    logging.info("This is the end")
    return None


def process_function(arn, repo, digest):
    # retrieve function configuration
    f = LDA.get_function(FunctionName=arn)
    logging.info(f"...IMAGE_URI:{f['Code']['ImageUri']}")
    match = re.search(r"^[^/]*/(.*)@(.*)$", f["Code"]["ImageUri"])

    # check repo
    logging.info(f"...IMA_REPO:{match.group(1)}")
    if match.group(1) == repo:
        # check digest
        logging.info(f"...IMA_DIGEST:{match.group(2)}")
        if match.group(2) == digest:
            logging.info("...Image already up-to-date")

        else:
            # update image
            target_uri = re.sub(r"@(.*)$", f"@{digest}", f["Code"]["ImageUri"])
            logging.info(f"...Updating image to {target_uri}...")
            LDA.update_function_code(FunctionName=arn, ImageUri=target_uri)


def process_task_definition(arn, repo, digest):
    # retrieve container definitions
    td = ECS.describe_task_definition(taskDefinition=arn)
    cds = td["taskDefinition"]["containerDefinitions"]
    changed = False
    for i, cd in enumerate(td["taskDefinition"]["containerDefinitions"]):
        logging.info(f"...IMAGE_URI:{cd['image']}")
        match = re.search(r"^[^/]*/(.*)@(.*)$", cd["image"])

        # check repo
        logging.info(f"...IMA_REPO:{match.group(1)}")
        if match.group(1) == repo:
            # check digest
            logging.info(f"...IMA_DIGEST:{match.group(2)}")
            if match.group(2) == digest:
                logging.info("...Image already up-to-date")

            else:
                # update container definition
                target_uri = re.sub(r"@(.*)$", f"@{digest}", cd["image"])
                logging.info(f"...Updating image to {target_uri}...")
                cds[i]["image"] = target_uri
                changed = True

    # eventually register new task definition revision
    if changed:
        logging.info("...Registering new revision")
        ntd = clean_task_definition(td["taskDefinition"], cds)
        ECS.register_task_definition(**ntd)
        if DISABLE_OLD_ECS == "on":
            logging.info("...Deregistering old revision")
            ECS.deregister_task_definition(taskDefinition=arn)
        return True
    else:
        return False


def update_services(families):
    # browse ecs clusters
    paginator = ECS.get_paginator("list_clusters")
    iterator = paginator.paginate()
    for page in iterator:
        logging.info("Browsing ecs task clusters...")
        for c in page["clusterArns"]:
            # browse services
            paginator_s = ECS.get_paginator("list_services")
            iterator_s = paginator_s.paginate(cluster=c)
            for page_s in iterator_s:
                logging.info("Browsing services...")
                for s in page_s["serviceArns"]:
                    # check task definition
                    srv = ECS.describe_services(cluster=c, services=[s])
                    s = srv["services"][0]["taskDefinition"].split(":")
                    family = s[5][16:]
                    logging.info(f"FAMILY:{family}")
                    if family in families:
                        # rolling update
                        logging.info(
                            f"...Updating service {srv['services'][0]['serviceName']}"
                        )
                        upd = ECS.update_service(
                            cluster=c,
                            service=srv["services"][0]["serviceName"],
                            taskDefinition=family,
                            forceNewDeployment=True,
                        )
                        if "service" in upd and "deployments" in upd["service"]:
                            for dep in upd["service"]["deployments"]:
                                if (
                                    "rolloutState" in dep
                                    and dep["rolloutState"] == "IN_PROGRESS"
                                ):
                                    logging.info(f"...DEPLOYMENT:{dep['id']}")
                        else:
                            logging.info("Unable to find deployment!")


def clean_task_definition(td, cds):
    if "taskDefinitionArn" in td:
        del td["taskDefinitionArn"]
    if "revision" in td:
        del td["revision"]
    if "status" in td:
        del td["status"]
    if "requiresAttributes" in td:
        del td["requiresAttributes"]
    if "compatibilities" in td:
        del td["compatibilities"]
    if "registeredAt" in td:
        del td["registeredAt"]
    if "registeredBy" in td:
        del td["registeredBy"]
    if "containerDefinitions" in td:
        td["containerDefinitions"] = cds
    return td
