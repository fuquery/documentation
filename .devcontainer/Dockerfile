FROM ghcr.io/fuquery/fedora_devcontainer:latest

RUN dnf install -y ruby pip ruby-devel redhat-rpm-config yarnpkg

RUN gem install --no-document rouge nokogiri

RUN yarn global add @antora/cli
RUN yarn global add @antora/site-generator
RUN yarn global add @antora/lunr-extension
RUN yarn global add @antora/collector-extension

RUN pip install --no-input --root-user-action=ignore pyyaml
RUN pip install --no-input --root-user-action=ignore git+https://github.com/tsche/claudoc.git@master