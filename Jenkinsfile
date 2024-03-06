#!/usr/bin/env groovy

import static uk.gov.landregistry.jenkins.pipeline.ClosureUtils.applicationPipelineConfig

// See https://internal-git-host/common-code/jenkins-pipelines/-/blob/master/vars/pythonExtendedPipeline.groovy
// Any parameter being set to the same as the default could be removed; it is there for clarity and learning purposes only
pythonExtendedPipeline applicationPipelineConfig {
  // dockerImageName 'flask-skeletonxl-api' // Default is same value as projectName
  // releaseBranchPrefix 'release/' // Default. Used for hotifixing the matching helm-chart release branch
  trunkBranch 'develop'
  // unitTestModules ([]) // Default

  devOpsNamespace 'llc-devops'
  dockerRegistry 'docker-registry/local-land-charges'
  projectName 'storage-api'
  pythonVersion '3.9'
  unitTestEnvironmentFile './unit-test-env.sh' // Default is /dev/null
  
  helmProject {
    chartPath 'local-land-charges/charts/storage-api'
    chartRepository 'git@internal-git-host:llc-beta/helm-charts.git'
    gitCredentialsId 'llc-deploy-key'
    trunkHelmUpdateBranch 'integration' // Target for updating the version, ignored in release branch hotfix scenario
  }

}
