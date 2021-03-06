from flask import current_app as app
from sqlalchemy.exc import IntegrityError
from .ext import db
from os import path
from .models import Challenge, Resource
from .core import hash_fleg
import json


def build_challenges():
    chal_path = path.join(app.root_path, "../",
                          app.config['CTF']['challenges'])
    categories = app.config['CTF']['categories']
    for c in categories:
        problem_config = path.join(chal_path, c, "problems.json")
        with open(problem_config, 'r') as config_file:
            try:
                config = json.load(config_file)
            except ValueError:
                raise ValueError("%s was malformed" % config_file)
            for problem in config["problems"]:
                # We put this first to avoid circular dependancies
                prereqs = set()
                if len(problem["prerequisites"]) > 0:
                    prereqs = Challenge.query.filter(
                        Challenge.title.in_(problem["prerequisites"])).all()
                    if len(problem["prerequisites"]) != len(prereqs):
                        raise ValueError("Prerequisite mismatch, %s" %
                                         problem["title"])
                challenge = Challenge(title=problem["title"],
                                      description=problem["description"],
                                      category=c,
                                      points=problem["points"],
                                      fleg_hash=hash_fleg(problem["fleg"]),
                                      prerequisites=set(prereqs))
                db.session.add(challenge)
                for file in problem["resources"]:
                    file_path = path.join(chal_path, c)
                    resource = Resource(name=file,
                                        path=file_path,
                                        challenge=challenge)
                    db.session.add(resource)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
