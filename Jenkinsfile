pipeline {

    agent any

    parameters {

        choice(
            name: 'ENVIRONMENT',
            choices: ['DEV', 'UAT', 'PRODUCTION'],
            description: 'Select deployment environment'
        )

        choice(
            name: 'ACTION',
            choices: ['DEPLOY', 'ROLLBACK'],
            description: 'Select deployment action'
        )

        string(
            name: 'VERSION',
            defaultValue: '1.0.0',
            description: 'Docker image version'
        )

        choice(
            name: 'RUN_TESTS',
            choices: ['YES', 'NO'],
            description: 'Run automated tests'
        )

        choice(
            name: 'CONFIRM_PROD',
            choices: ['NO', 'YES'],
            description: 'Required for production deployment'
        )
    }

    stages {

        stage('Resolve Deployment Configuration') {

            steps {

                script {

                    if (params.ENVIRONMENT == 'DEV') {

                        env.GIT_BRANCH_NAME = 'develop'
                        env.PROFILE = 'dev'
                        env.APP_CONTAINER = 'customer-app-dev'
                        env.DB_CONTAINER = 'customer-db-dev'
                        env.NETWORK_NAME = 'customer-dev-net'
                        env.HOST_PORT = '8081'

                    } else if (params.ENVIRONMENT == 'UAT') {

                        env.GIT_BRANCH_NAME = 'release'
                        env.PROFILE = 'uat'
                        env.APP_CONTAINER = 'customer-app-uat'
                        env.DB_CONTAINER = 'customer-db-uat'
                        env.NETWORK_NAME = 'customer-uat-net'
                        env.HOST_PORT = '8082'

                    } else {

                        env.GIT_BRANCH_NAME = 'main'
                        env.PROFILE = 'prod'
                        env.APP_CONTAINER = 'customer-app-prod'
                        env.DB_CONTAINER = 'customer-db-prod'
                        env.NETWORK_NAME = 'customer-prod-net'
                        env.HOST_PORT = '8083'
                    }

                    if (
                        params.ENVIRONMENT == 'PRODUCTION' &&
                        params.CONFIRM_PROD != 'YES'
                    ) {
                        error(
                            'Production deployment requires CONFIRM_PROD=YES'
                        )
                    }

                    if (!params.VERSION?.trim()) {
                        error('VERSION cannot be empty')
                    }

                    echo "========== DEPLOYMENT CONFIGURATION =========="

                    echo "Environment  : ${params.ENVIRONMENT}"
                    echo "Action       : ${params.ACTION}"
                    echo "Version      : ${params.VERSION}"
                    echo "Git Branch   : ${env.GIT_BRANCH_NAME}"
                    echo "Docker Profile: ${env.PROFILE}"
                    echo "App Container: ${env.APP_CONTAINER}"
                    echo "DB Container : ${env.DB_CONTAINER}"
                    echo "Network      : ${env.NETWORK_NAME}"
                    echo "Host Port    : ${env.HOST_PORT}"
                    echo "Run Tests    : ${params.RUN_TESTS}"

                    echo "==============================================="
                }
            }
        }


        stage('Checkout Selected Branch') {

            steps {

                bat """
                    git fetch origin ${env.GIT_BRANCH_NAME}
                    git checkout -B ${env.GIT_BRANCH_NAME} origin/${env.GIT_BRANCH_NAME}
                """

                bat """
                    echo Current commit:
                    git rev-parse HEAD
                """
            }
        }


        stage('Run Tests') {

            when {

                expression {
                    params.RUN_TESTS == 'YES'
                }
            }

            steps {

                echo "Running tests inside Python Docker container..."

                bat """
                    docker run --rm ^
                    -v "%CD%:/workspace" ^
                    -w /workspace ^
                    python:3.12-slim ^
                    sh -c "pip install --no-cache-dir -r app/requirements.txt && pip install --no-cache-dir pytest && python -m pytest"
                """
            }
        }


        stage('Build Docker Image') {

            when {

                expression {
                    params.ACTION == 'DEPLOY'
                }
            }

            steps {

                echo "Building customer application image..."

                bat """
                    docker build -t customer-app:${params.VERSION} .
                """

                echo "Validating Docker image..."

                bat """
                    docker image inspect customer-app:${params.VERSION}
                """
            }
        }


        stage('Deploy Environment') {

            when {

                expression {
                    params.ACTION == 'DEPLOY'
                }
            }

            steps {

                withCredentials([
                    string(
                        credentialsId: 'customer-db-password',
                        variable: 'DB_PASSWORD'
                    )
                ]) {

                    echo "Deploying ${params.ENVIRONMENT} environment..."

                    bat """
                        set VERSION=${params.VERSION}
                        set DB_PASSWORD=%DB_PASSWORD%

                        docker compose --profile ${env.PROFILE} down

                        docker compose --profile ${env.PROFILE} up -d
                    """
                }
            }
        }


        stage('Validate Deployment') {

            when {

                expression {
                    params.ACTION == 'DEPLOY'
                }
            }

            steps {

                echo "Waiting for containers to become healthy..."

                bat """
                    timeout /t 20 /nobreak
                """

                echo "Checking running containers..."

                bat """
                    docker ps
                """

                echo "Checking application container..."

                bat """
                    docker inspect ${env.APP_CONTAINER}
                """

                echo "Checking database container..."

                bat """
                    docker inspect ${env.DB_CONTAINER}
                """

                echo "Checking application health..."

                bat """
                    curl --fail http://localhost:${env.HOST_PORT}/health
                """

                echo "Checking database connectivity..."

                bat """
                    curl --fail http://localhost:${env.HOST_PORT}/db-health
                """

                echo "Checking application version..."

                bat """
                    curl --fail http://localhost:${env.HOST_PORT}/version
                """

                echo "Deployment validation completed."
            }
        }


        stage('Rollback') {

            when {

                expression {
                    params.ACTION == 'ROLLBACK'
                }
            }

            steps {

                withCredentials([
                    string(
                        credentialsId: 'customer-db-password',
                        variable: 'DB_PASSWORD'
                    )
                ]) {

                    echo "Starting rollback..."

                    bat """
                        set VERSION=${params.VERSION}
                        set DB_PASSWORD=%DB_PASSWORD%

                        docker compose --profile ${env.PROFILE} down

                        docker compose --profile ${env.PROFILE} up -d
                    """
                }

                bat """
                    timeout /t 20 /nobreak
                """

                bat """
                    docker ps
                """

                bat """
                    curl --fail http://localhost:${env.HOST_PORT}/health
                """

                bat """
                    curl --fail http://localhost:${env.HOST_PORT}/db-health
                """

                echo "Rollback validation completed."
            }
        }
    }


    post {

        success {

            echo "==============================================="
            echo "DEPLOYMENT SUCCESSFUL"
            echo "Environment: ${params.ENVIRONMENT}"
            echo "Version: ${params.VERSION}"
            echo "==============================================="
        }

        failure {

            echo "==============================================="
            echo "DEPLOYMENT FAILED"
            echo "Environment: ${params.ENVIRONMENT}"
            echo "Version: ${params.VERSION}"
            echo "==============================================="
        }

        always {

            echo "Final Docker container status:"

            bat """
                docker ps -a
            """
        }
    }
}