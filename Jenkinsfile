pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '15'))
    }

    environment {
        REGISTRY = 'docker.io'
        IMAGE_REPO = 'dhanushm18/research-agent'
        DOCKER_CREDENTIALS_ID = 'dockerhub-creds'
        DEPLOY_SSH_CREDENTIALS_ID = 'deploy-ssh-key'
        DEPLOY_HOST = ''
        DEPLOY_USER = ''
        DEPLOY_PATH = '/opt/research-agent'
        APP_PORT = '8000'
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Prepare Metadata') {
            steps {
                script {
                    env.GIT_SHA = isUnix()
                        ? sh(script: 'git rev-parse --short=8 HEAD', returnStdout: true).trim()
                        : bat(script: '@git rev-parse --short=8 HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_SHA}"
                    env.IS_MAIN = (env.BRANCH_NAME ?: '') == 'main' ? 'true' : 'false'
                    env.IS_TAG = env.TAG_NAME ? 'true' : 'false'
                    env.SHOULD_PUBLISH = (env.IS_MAIN == 'true' || env.IS_TAG == 'true') ? 'true' : 'false'
                }
            }
        }

        stage('Set Up Python') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            python3 --version
                            python3 -m venv .venv
                            . .venv/bin/activate
                            python -m pip install --upgrade pip
                            pip install -r requirements.txt
                        '''
                    } else {
                        bat '''
                            python --version
                            python -m venv .venv
                            call .venv\\Scripts\\activate
                            python -m pip install --upgrade pip
                            pip install -r requirements.txt
                        '''
                    }
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            . .venv/bin/activate
                            pytest pytests
                        '''
                    } else {
                        bat '''
                            call .venv\\Scripts\\activate
                            pytest pytests
                        '''
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def image = "${env.IMAGE_REPO}:${env.IMAGE_TAG}"
                    if (isUnix()) {
                        sh "docker build -t ${image} -t ${env.IMAGE_REPO}:latest ."
                    } else {
                        bat "docker build -t ${image} -t ${env.IMAGE_REPO}:latest ."
                    }
                }
            }
        }

        stage('Push Docker Image') {
            when {
                expression { env.SHOULD_PUBLISH == 'true' }
            }
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: env.DOCKER_CREDENTIALS_ID,
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        if (isUnix()) {
                            sh '''
                                echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                                docker push "${IMAGE_REPO}:${IMAGE_TAG}"
                                docker push "${IMAGE_REPO}:latest"
                                docker logout
                            '''
                        } else {
                            bat '''
                                @echo %DOCKER_PASS%| docker login -u %DOCKER_USER% --password-stdin
                                docker push %IMAGE_REPO%:%IMAGE_TAG%
                                docker push %IMAGE_REPO%:latest
                                docker logout
                            '''
                        }
                    }
                }
            }
        }

        stage('Deploy') {
            when {
                expression {
                    env.IS_MAIN == 'true' &&
                    env.DEPLOY_HOST?.trim() &&
                    env.DEPLOY_USER?.trim()
                }
            }
            steps {
                script {
                    withCredentials([sshUserPrivateKey(
                        credentialsId: env.DEPLOY_SSH_CREDENTIALS_ID,
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )]) {
                        def remoteScript = """
                            set -e
                            cd ${env.DEPLOY_PATH}
                            docker login -u ${'$'}{DOCKER_USER} -p ${'$'}{DOCKER_PASS} ${env.REGISTRY}
                            docker pull ${env.IMAGE_REPO}:${env.IMAGE_TAG}
                            export IMAGE_REPO=${env.IMAGE_REPO}
                            export IMAGE_TAG=${env.IMAGE_TAG}
                            docker compose up -d
                            docker image prune -f
                        """.trim()

                        withCredentials([usernamePassword(
                            credentialsId: env.DOCKER_CREDENTIALS_ID,
                            usernameVariable: 'DOCKER_USER',
                            passwordVariable: 'DOCKER_PASS'
                        )]) {
                            if (isUnix()) {
                                writeFile file: 'deploy.sh', text: remoteScript + '\n'
                                sh '''
                                    chmod 600 "$SSH_KEY"
                                    scp -i "$SSH_KEY" -o StrictHostKeyChecking=no deploy.sh "$SSH_USER@$DEPLOY_HOST:$DEPLOY_PATH/deploy.sh"
                                    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$DEPLOY_HOST" "cd $DEPLOY_PATH && chmod +x deploy.sh && ./deploy.sh"
                                '''
                            } else {
                                writeFile file: 'deploy.sh', text: remoteScript.replace('\n', '\r\n') + '\r\n'
                                bat '''
                                    scp -i "%SSH_KEY%" -o StrictHostKeyChecking=no deploy.sh %SSH_USER%@%DEPLOY_HOST%:%DEPLOY_PATH%/deploy.sh
                                    ssh -i "%SSH_KEY%" -o StrictHostKeyChecking=no %SSH_USER%@%DEPLOY_HOST% "cd %DEPLOY_PATH% && chmod +x deploy.sh && ./deploy.sh"
                                '''
                            }
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                if (isUnix()) {
                    sh 'docker logout || true'
                } else {
                    bat 'docker logout'
                }
            }
            cleanWs()
        }
    }
}
