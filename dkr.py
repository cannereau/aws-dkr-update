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

            # browse task definitions
            if UPDATE_ECS == "on":
                tds = []
                tag_image = f"{event['detail']['repository-name']}:{ENV_TAG}"
                paginator = ECS.get_paginator("list_task_definitions")
                iterator = paginator.paginate(status="ACTIVE")
                for page in iterator:
                    logging.info("Browsing ecs task definitions...")
                    for arn in page["taskDefinitionArns"]:
                        td = ECS.describe_task_definition(taskDefinition=arn)
                        for cd in td["containerDefinitions"]:
                            if arn not in tds:
                                logging.info(f"...IMAGE_URI:{cd['image']}")
                                match = re.search(r"^[^/]*/([^:]*:[^:]*)$", cd["image"])
                                if match is not None and match.group(1) == tag_image:
                                    logging.info(f"...FAMILY:{td['family']}")
                                    tds.append(td["family"])
                process_task_definitions(tds)

        else:
            logging.info("Invalid Image Tag")

    else:
        logging.info("Invalid Event")

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


def process_task_definitions(families):
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
                    logging.info(f"...TASK_DEF:{srv['services'][0]['taskDefinition']}")
                    if srv["services"][0]["taskDefinition"] in families:
                        # rolling update
                        logging.info(
                            f"...Updating service {srv['services'][0]['serviceName']}"
                        )
                        response = ECS.update_service(
                            cluster=c,
                            service=srv["services"][0]["serviceName"],
                            taskDefinition=srv["services"][0]["taskDefinition"],
                        )
                        logging.info(response)
