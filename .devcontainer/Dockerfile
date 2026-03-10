FROM antora/antora
ARG MRDOCS_VERSION=0.8.0


RUN apk add --no-cache \
bash \
curl \
git \
ruby \
ruby-dev \
build-base \
libxml2-dev \
libxslt-dev \
tar

RUN gem install --no-document rouge nokogiri

RUN apk add --no-cache python3 py3-pip

RUN pip install pyyaml
RUN pip install watchdog

RUN yarn global add @antora/lunr-extension
RUN yarn global add @antora/collector-extension

RUN apk add --no-cache curl tar xz \
 && curl -L https://github.com/cppalliance/mrdocs/releases/download/v${MRDOCS_VERSION}/MrDocs-${MRDOCS_VERSION}-Linux.tar.xz \
    -o /tmp/mrdocs.tar.xz \
 && mkdir -p /opt/mrdocs \
 && tar -xJf /tmp/mrdocs.tar.xz -C /opt/mrdocs --strip-components=1 \
 && rm /tmp/mrdocs.tar.xz \
 && ln -s /opt/mrdocs/bin/mrdocs /usr/local/bin/mrdocs

# Patch code blocks for use with rouge
COPY .devcontainer/code-block.patch /opt/mrdocs/code-block.patch
RUN patch -p1 -d /opt/mrdocs < /opt/mrdocs/code-block.patch
RUN rm /opt/mrdocs/code-block.patch

USER node

