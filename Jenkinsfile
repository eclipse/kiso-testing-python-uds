pipeline
{
    agent
    {
        kubernetes
        {
            containerTemplate
            {
                name 'kiso-build-env'
                image 'eclipse/kiso-build-env:v0.1.0'
                alwaysPullImage 'true'
                ttyEnabled true
                resourceRequestCpu '2'
                resourceLimitCpu '2'
                resourceRequestMemory '8Gi'
                resourceLimitMemory '8Gi'
            }
        }
    }
    options
    {
        timeout(time: 2, unit: 'HOURS')
    }
    stages
    {
        stage('Release')
        {
            when
            {
                buildingTag()
            }
            steps
            {
                script
                {
                    sh "pip install twine"
                    sh "pip install wheel"
                    sh "python setup.py sdist"
                    sh "python setup.py bdist_wheel"
                    sh "twine upload dist/*"
                    withCredentials([string(
                        credentialsId: 'pypi-bot-token',
                        variable: 'token')]) {

                            sh "twine upload\
                                    --verbose \
                                    --username __token__\
                                    --password ${token}\
                                    dist/*"
                        }
                }
            }
        } // Release
    } // stages

    post // Called at very end of the script to notify developer and github about the result of the build
    {
        success
        {
            cleanWs()
        }
        unstable
        {
            notifyFailed()
        }
        failure
        {
            notifyFailed()
        }
        aborted
        {
            notifyAbort()
        }
    }
} // pipeline


def notifyFailed()
{
    emailext (subject: "Job '${env.JOB_NAME}' (${env.BUILD_NUMBER}) is failing",
                body: "Oups, something went wrong with ${env.BUILD_URL}... We are looking forward for your fix!",
                recipientProviders: [[$class: 'CulpritsRecipientProvider'],
                                    [$class: 'DevelopersRecipientProvider'],
                                    [$class: 'RequesterRecipientProvider']])
}

def notifyAbort()
{
    emailext (subject: "Job '${env.JOB_NAME}' (${env.BUILD_NUMBER}) was aborted",
                body: "Oups, something went wrong with ${env.BUILD_URL}... We are looking forward for your fix!",
                recipientProviders: [[$class: 'CulpritsRecipientProvider'],
                                    [$class: 'DevelopersRecipientProvider'],
                                    [$class: 'RequesterRecipientProvider']])
}
