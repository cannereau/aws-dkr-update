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
UPDATE_LAMBDA = "off"
if "UPDATE_LAMBDA" in os.environ:
    UPDATE_LAMBDA = os.environ["UPDATE_LAMBDA"]

# init boto3 clients
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
