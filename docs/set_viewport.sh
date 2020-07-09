#!/bin/bash
find ./build/html -name "*.html" | xargs sed -i -e 's/<head>/<head><meta name="viewport" content="width=device-width, initial-scale=1.0">/g'

echo "@media screen and (max-width: 480px) {
    div.document,
    div.documentwrapper,
    div.bodywrapper {
        margin: 0 !important;
        width: 100%;
    }

    div.sphinxsidebar,
    #top-link {
        display: none;
    }
}" >> ./build/html/_static/basic.css
