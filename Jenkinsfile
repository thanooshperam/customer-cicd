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


        /*
         * ============================================================
         * RECORD PREVIOUS PRODUCTION IMAGE
         * ============================================================
         *
         * This stage is required only for a PRODUCTION deployment.
         *
         * DEV and UAT do not need a previous production image because
         * automatic production rollback is not being performed there.
         */

        stage('Record Previous Production Image') {

            when {

                allOf {

                    expression {
                        params.ACTION == 'DEPLOY'
                    }

                    expression {
                        params.ENVIRONMENT == 'PRODUCTION'
                    }
                }
            }

            steps {

                script {

                    echo "Recording currently running production image..."

                    def previousImage = bat(
                        script: """
                            @echo off
                            docker inspect --format="{{.Config.Image}}" ${env.APP_CONTAINER}
                        """,
                        returnStdout: true
                    ).trim()


                    if (!previousImage) {

                        error(
                            "Unable to determine previous image for ${env.APP_CONTAINER}"
                        )
                    }


                    echo "Previous Image : ${previousImage}"


                    if (!previousImage.contains(':')) {

                        error(
                            "Previous image does not contain a version tag: ${previousImage}"
                        )
                    }


                    env.PREVIOUS_IMAGE = previousImage

                    env.PREVIOUS_VERSION =
                        previousImage.substring(
                            previousImage.lastIndexOf(':') + 1
                        )


                    echo "Previous Version: ${env.PREVIOUS_VERSION}"
                }
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

                script {

                    /*
                     * Mark deployment as started before changing
                     * the running environment.
                     *
                     * If anything after this point fails,
                     * the post-failure section can restore
                     * the previous production version.
                     */

                    env.DEPLOYMENT_STARTED = 'true'
                }


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


        /*
         * ============================================================
         * MANUAL ROLLBACK
         * ============================================================
         *
         * This is the explicit ROLLBACK action selected by the user.
         *
         * Example:
         * ENVIRONMENT = PRODUCTION
         * ACTION      = ROLLBACK
         * VERSION     = 1.0.0
         */

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

                    echo "Starting manual rollback..."
                    echo "Rollback Version: ${params.VERSION}"

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


                echo "Checking rollback application version..."

                bat """
                    curl --fail http://localhost:${env.HOST_PORT}/version
                """


                echo "Rollback validation completed."
            }
        }
    }


    /*
     * ================================================================
     * POST ACTIONS
     * ================================================================
     */

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


            script {

                /*
                 * ====================================================
                 * AUTOMATIC PRODUCTION ROLLBACK
                 * ====================================================
                 *
                 * Automatic rollback happens only when:
                 *
                 * 1. ACTION is DEPLOY
                 * 2. ENVIRONMENT is PRODUCTION
                 * 3. Deployment actually started
                 * 4. Previous production image was recorded
                 *
                 * If tests fail before deployment starts,
                 * production is NOT touched.
                 */

                if (
                    params.ACTION == 'DEPLOY' &&
                    params.ENVIRONMENT == 'PRODUCTION' &&
                    env.DEPLOYMENT_STARTED == 'true' &&
                    env.PREVIOUS_VERSION?.trim()
                ) {

                    echo "==============================================="
                    echo "       AUTOMATIC ROLLBACK STARTING"
                    echo "==============================================="

                    echo "Failed Version  : ${params.VERSION}"
                    echo "Previous Version: ${env.PREVIOUS_VERSION}"
                    echo "Previous Image  : ${env.PREVIOUS_IMAGE}"


                    withCredentials([
                        string(
                            credentialsId: 'customer-db-password',
                            variable: 'DB_PASSWORD'
                        )
                    ]) {

                        bat """
                            set "VERSION=${env.PREVIOUS_VERSION}"
                            set "DB_PASSWORD=%DB_PASSWORD%"

                            echo Restoring previous production version...

                            "C:\\Users\\Administrator\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker-compose.exe" down ${env.COMPOSE_SERVICES}

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


                    echo "Checking restored application version..."

                    bat """
                        curl --fail http://localhost:${env.HOST_PORT}/version
                    """


                    echo "==============================================="
                    echo "       AUTOMATIC ROLLBACK COMPLETED"
                    echo "==============================================="

                    echo "Restored Version: ${env.PREVIOUS_VERSION}"

                    echo "The deployment remains FAILED because the"
                    echo "requested production deployment did not pass validation."

                    echo "==============================================="

                } else {

                    echo "Automatic production rollback was not required."
                }
            }
        }


        always {

            echo "Final Docker container status:"

            bat """
                docker ps -a
            """
        }
    }
}