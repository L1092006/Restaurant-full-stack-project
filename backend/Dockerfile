FROM ubuntu:26.04
LABEL "Author"="Loc"
LABEL "Project"="Restaurant"
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install git -y && apt install python3-venv -y
ADD . /srv
WORKDIR /srv
RUN chmod 774 setup.sh
EXPOSE 8000
ENTRYPOINT [ "./setup.sh"]

