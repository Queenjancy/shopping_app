# Shopping list for App Engine

### Live demo

https://shopping-list-157818.appspot.com/

### Installation instructions

1. (If you already have Python App Engine SDK installed, skip to step 2.)
Follow instructions here: https://cloud.google.com/appengine/docs/python/download

    ```
    ./google-cloud-sdk/install.sh
    ./google-cloud-sdk/bin/gcloud init
    gcloud components install app-engine-python
    ```

2. Get the code

    ```
    git clone https://github.com/j4sond3ak1n/shopping-app.git
    cd shopping-list
    ```

3. Run code locally

    ```
    dev_appserver.py app.yaml
    ```

4. Open browser at http://localhost:8080 and ensure it works
5. Stop local server
6. Create project using Google Cloud Console https://console.cloud.google.com/iam-admin/projects
7. Upload code and get app running

    ```
    gcloud app deploy
    ```

8. Open https://(project id from step 6).appspot.com
