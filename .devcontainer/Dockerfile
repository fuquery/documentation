FROM antora/antora


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

RUN npm install -g @antora/lunr-extension

USER node

