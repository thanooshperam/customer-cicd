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
                        env.APP_CONTAINER = 'customer-app-dev'
                        env.DB_CONTAINER = 'customer-db-dev'
                        env.COMPOSE_SERVICES = 'customer-db-dev customer-app-dev'
                        env.NETWORK_NAME = 'customer-dev-net'
                        env.HOST_PORT = '8081'
                        env.ENV_VALUE = 'DEV'

                    } else if (params.ENVIRONMENT == 'UAT') {

                        env.GIT_BRANCH_NAME = 'release'
                        env.APP_CONTAINER = 'customer-app-uat'
                        env.DB_CONTAINER = 'customer-db-uat'
                        env.COMPOSE_SERVICES = 'customer-db-uat customer-app-uat'
                        env.NETWORK_NAME = 'customer-uat-net'
                        env.HOST_PORT = '8082'
                        env.ENV_VALUE = 'UAT'

                    } else {

                        env.GIT_BRANCH_NAME = 'main'
                        env.APP_CONTAINER = 'customer-app-prod'
                        env.DB_CONTAINER = 'customer-db-prod'
                        env.COMPOSE_SERVICES = 'customer-db-prod customer-app-prod'
                        env.NETWORK_NAME = 'customer-prod-net'
                        env.HOST_PORT = '8083'
                        env.ENV_VALUE = 'PRODUCTION'
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


                    echo "==============================================="
                    echo "       DEPLOYMENT CONFIGURATION"
                    echo "==============================================="

                    echo "Environment    : ${params.ENVIRONMENT}"
                    echo "Action         : ${params.ACTION}"
                    echo "Version        : ${params.VERSION}"
                    echo "Git Branch     : ${env.GIT_BRANCH_NAME}"
                    echo "App Container  : ${env.APP_CONTAINER}"
                    echo "DB Container   : ${env.DB_CONTAINER}"
                    echo "Network        : ${env.NETWORK_NAME}"
                    echo "Host Port      : ${env.HOST_PORT}"
                    echo "Environment Val: ${env.ENV_VALUE}"
                    echo "Run Tests      : ${params.RUN_TESTS}"

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

                echo "Running automated tests..."

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

                echo "Building Docker image..."

                bat """
                    docker build -t customer-app:${params.VERSION} .
                """

                echo "Checking Docker image..."

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

                    echo "Deploying ${params.ENVIRONMENT}..."

                    bat """
                        set "VERSION=${params.VERSION}"
                        set "DB_PASSWORD=%DB_PASSWORD%"

                        echo Using Docker Compose:

                        "C:\\Users\\Administrator\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker-compose.exe" version

                        echo Stopping existing environment...

                        "C:\\Users\\Administrator\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker-compose.exe" down ${env.COMPOSE_SERVICES}

                        echo Starting environment...

                        "C:\\Users\\Administrator\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker-compose.exe" up -d ${env.COMPOSE_SERVICES}
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

                echo "Waiting for containers to start..."

                bat """
                    ping 127.0.0.1 -n 21 > nul
                """


                echo "Checking Docker containers..."

                bat """
                    docker ps
                """


                echo "Checking application container..."

                bat """
                    docker inspect --format="{{.Name}} | Status={{.State.Status}} | Health={{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}" ${env.APP_CONTAINER}
                """


                echo "Checking database container..."

                bat """
                    docker inspect --format="{{.Name}} | Status={{.State.Status}} | Health={{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}" ${env.DB_CONTAINER}
                """


                echo "Checking Docker network..."

                bat """
                    docker network inspect ${env.NETWORK_NAME}
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


                echo "Checking application environment..."

                bat """
                    curl --fail http://localhost:${env.HOST_PORT}/
                """


                echo "Checking requested Docker image..."

                bat """
                    docker image inspect customer-app:${params.VERSION}
                """


                echo "Deployment validation completed successfully."
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
                        set "VERSION=${params.VERSION}"
                        set "DB_PASSWORD=%DB_PASSWORD%"

                        echo Using Docker Compose:

                        "C:\\Users\\Administrator\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker-compose.exe" version

                        echo Stopping current environment...

                        "C:\\Users\\Administrator\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker-compose.exe" down ${env.COMPOSE_SERVICES}

                        echo Starting rollback version...

                        "C:\\Users\\Administrator\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker-compose.exe" up -d ${env.COMPOSE_SERVICES}
                    """
                }


                echo "Waiting for rollback containers..."

                bat """
                    ping 127.0.0.1 -n 21 > nul
                """


                echo "Checking rollback containers..."

                bat """
                    docker ps
                """


                echo "Checking rollback application health..."

                bat """
                    curl --fail http://localhost:${env.HOST_PORT}/health
                """


                echo "Checking rollback database connectivity..."

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
            echo "       DEPLOYMENT SUCCESSFUL"
            echo "==============================================="

            echo "Environment : ${params.ENVIRONMENT}"
            echo "Action      : ${params.ACTION}"
            echo "Version     : ${params.VERSION}"

            echo "==============================================="
        }


        failure {

            echo "==============================================="
            echo "       DEPLOYMENT FAILED"
            echo "==============================================="

            echo "Environment : ${params.ENVIRONMENT}"
            echo "Action      : ${params.ACTION}"
            echo "Version     : ${params.VERSION}"

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