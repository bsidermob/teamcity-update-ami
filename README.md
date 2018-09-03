# teamcity-update-ami

It's a Python script which updates AMI ID for a particular cloud profile in TeamCity
which is meant to run as a part of CI/CD pipeline after agent images are built.

Creation of it was inspired by this:
https://blog.grakn.ai/automated-aws-ami-builds-for-jenkins-agents-with-packer-e569630b1f8e
Kudos to the author above as his script works very nicely in Jenkins.

As I couldn't find anything similar for TeamCity, I made my own version of it.
It's simpler than the Jenkins version from the link above but still does the job.
