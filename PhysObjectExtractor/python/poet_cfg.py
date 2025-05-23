from __future__ import print_function

import sys

import FWCore.ParameterSet.Config as cms
import FWCore.ParameterSet.Types as CfgTypes
import FWCore.PythonUtilities.LumiList as LumiList
from FWCore.ParameterSet.VarParsing import VarParsing

# ---- sys.argv takes the parameters given as input cmsRun PhysObjectExtractor/python/poet_cfg.py <isData (default=False)>
# ----  e.g: cmsRun PhysObjectExtractor/python/poet_cfg.py True
# ---- NB the first two parameters are always "cmsRun" and the config file name
# ---- Work with data (if False, assumed MC simulations)
# ---- This needs to be in agreement with the input files/datasets below.
options = VarParsing("analysis")
isData = False
if len(sys.argv) > 2:
    try:
        isData = eval(sys.argv[2])
        sys.argv.pop(2)
        print("isData is set to ", isData)

    except:
        pass

options.parseArguments()

isMC = True
if isData:
    isMC = False

process = cms.Process("POET")

# ---- Configure the framework messaging system
# ---- https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideMessageLogger
process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.threshold = "WARNING"
process.MessageLogger.categories.append("POET")
process.MessageLogger.cerr.INFO = cms.untracked.PSet(limit=cms.untracked.int32(-1))
process.options = cms.untracked.PSet(wantSummary=cms.untracked.bool(True))

# ---- Select the maximum number of events to process (if -1, run over all events)
process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(-1))

# ---- Needed configuration for dealing with transient tracks if required
process.load("TrackingTools/TransientTrack/TransientTrackBuilder_cfi")
process.load("Configuration.Geometry.GeometryIdeal_cff")
process.load("Configuration.StandardSequences.MagneticField_cff")

# ---- Define the test source files to be read using the xrootd protocol (root://), or local files (file:)
process.source = cms.Source(
    "PoolSource",
    fileNames=cms.untracked.vstring(
        "root://eospublic.cern.ch//eos/opendata/cms/mc/RunIIFall15MiniAODv2/TTbarDMJets_scalar_Mchi-1_Mphi-500_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/70000/48EC4AA8-1EB9-E511-9248-441EA1733CDA.root"
    ),
)
if isData:
    process.source.fileNames = cms.untracked.vstring(
        "root://eospublic.cern.ch//eos/opendata/cms/Run2015D/SingleElectron/MINIAOD/08Jun2016-v1/10000/001A703B-B52E-E611-BA13-0025905A60B6.root"
    )

    # ---- Apply the data quality JSON file filter. This example is for 2015 data
    # ---- It needs to be done after the process.source definition
    # ---- Make sure the location of the file agrees with your setup
    goodJSON = "data/Cert_13TeV_16Dec2015ReReco_Collisions15_25ns_JSON_v2.txt"
    myLumis = LumiList.LumiList(filename=goodJSON).getCMSSWString().split(",")
    process.source.lumisToProcess = CfgTypes.untracked(CfgTypes.VLuminosityBlockRange())
    process.source.lumisToProcess.extend(myLumis)


# ---- These two lines are needed if you require access to the conditions database. E.g., to get jet energy corrections, trigger prescales, etc.
process.load("Configuration.StandardSequences.Services_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
# ---- Uncomment and arrange a line like this if you are getting access to the conditions database through CVMFS snapshot files (requires installing CVMFS client)
# process.GlobalTag.connect = cms.string('sqlite_file:/cvmfs/cms-opendata-conddb.cern.ch/76X_dataRun2_16Dec2015_v0.db')
# ---- If the container has local DB files available, uncomment lines like the ones below instead of the corresponding lines above
if isData:
    process.GlobalTag.connect = cms.string(
        "sqlite_file:/cvmfs/cms-opendata-conddb.cern.ch/76X_dataRun2_16Dec2015_v0.db"
    )
else:
    process.GlobalTag.connect = cms.string(
        "sqlite_file:/cvmfs/cms-opendata-conddb.cern.ch/76X_mcRun2_asymptotic_RunIIFall15DR76_v1.db"
    )
# ---- The global tag must correspond to the needed epoch (comment out if no conditions needed)
if isData:
    process.GlobalTag.globaltag = "76X_dataRun2_16Dec2015_v0"
else:
    process.GlobalTag.globaltag = "76X_mcRun2_asymptotic_RunIIFall15DR76_v1"

# ----- Configure POET analyzers -----#
process.myelectrons = cms.EDAnalyzer(
    "ElectronAnalyzer",
    electrons=cms.InputTag("slimmedElectrons"),
    vertices=cms.InputTag("offlineSlimmedPrimaryVertices"),
)

process.mymuons = cms.EDAnalyzer(
    "MuonAnalyzer",
    muons=cms.InputTag("slimmedMuons"),
    vertices=cms.InputTag("offlineSlimmedPrimaryVertices"),
)

# process.mytaus = cms.EDAnalyzer("TauAnalyzer", taus=cms.InputTag("slimmedTaus"))

# process.myphotons = cms.EDAnalyzer(
#     "PhotonAnalyzer", photons=cms.InputTag("slimmedPhotons")
# )

# ---- Module to store trigger objects (functional but not fully developed yet) -------#
# process.mytrigobjs = cms.EDAnalyzer('TriggObjectAnalyzer', objects = cms.InputTag("selectedPatTrigger"))

# ---- Example on how to add trigger information
# ---- To include it, uncomment the lines below and include the
# ---- module in the final path
# process.mytriggers = cms.EDAnalyzer('TriggerAnalyzer',
#                              processName = cms.string("HLT"),
#                              #---- These are example of OR of triggers for 2015
#                              #---- Wildcards * and ? are accepted (with usual meanings)
#                              #---- If left empty, all triggers will run
#                              triggerPatterns = cms.vstring("HLT_IsoMu20_v*","HLT_IsoTkMu20_v*"),
#                              triggerResults = cms.InputTag("TriggerResults","","HLT")
#                              )


process.mypvertex = cms.EDAnalyzer(
    "VertexAnalyzer",
    vertices=cms.InputTag("offlineSlimmedPrimaryVertices"),
    beams=cms.InputTag("offlineBeamSpot"),
)

process.mygenparticle = cms.EDAnalyzer(
    "GenParticleAnalyzer",
    pruned=cms.InputTag("prunedGenParticles"),
    # ---- Collect particles with specific "status:pdgid"
    # ---- if 0:0, collect them all
    input_particle=cms.vstring("0:0"),
)

process.myneutrinos = cms.EDAnalyzer(
    "GenParticleAnalyzer",
    pruned=cms.InputTag("prunedGenParticles"),
    input_particle=cms.vstring("1:12", "1:-12", "1:14", "1:-14", "1:16"),
)


# ----- Begin Jet correction setup -----#
JecString = "MC"
if isData:
    JecString = "DATA"

from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import (
    updatedPatJetCorrFactors,
)
from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cfi import updatedPatJets
from PhysicsTools.SelectorUtils.pfJetIDSelector_cfi import pfJetIDSelector

# ----- Apply the noise jet ID filter -----#
process.looseAK4Jets = cms.EDFilter(
    "PFJetIDSelectionFunctorFilter",
    filterParams=pfJetIDSelector.clone(),
    src=cms.InputTag("slimmedJets"),
)
process.looseAK8Jets = cms.EDFilter(
    "PFJetIDSelectionFunctorFilter",
    filterParams=pfJetIDSelector.clone(),
    src=cms.InputTag("slimmedJetsAK8"),
)

# ----- Apply the final jet energy corrections for 2015 -----#
process.patJetCorrFactorsReapplyJEC = updatedPatJetCorrFactors.clone(
    src=cms.InputTag("looseAK4Jets")
)
if isData:
    process.patJetCorrFactorsReapplyJEC.levels.append("L2L3Residual")

process.slimmedJetsNewJEC = updatedPatJets.clone(
    jetSource=cms.InputTag("looseAK4Jets"),
    jetCorrFactorsSource=cms.VInputTag(cms.InputTag("patJetCorrFactorsReapplyJEC")),
)
process.patJetCorrFactorsReapplyJECAK8 = updatedPatJetCorrFactors.clone(
    src=cms.InputTag("looseAK8Jets"),
    levels=["L1FastJet", "L2Relative", "L3Absolute"],
    payload="AK8PFchs",
)
if isData:
    process.patJetCorrFactorsReapplyJECAK8.levels.append("L2L3Residual")

process.slimmedJetsAK8NewJEC = updatedPatJets.clone(
    jetSource=cms.InputTag("looseAK8Jets"),
    jetCorrFactorsSource=cms.VInputTag(cms.InputTag("patJetCorrFactorsReapplyJECAK8")),
)

# ----- Configure the POET jet analyzers -----#
process.myjets = cms.EDAnalyzer(
    "JetAnalyzer",
    jets=cms.InputTag("slimmedJetsNewJEC"),
    genParticles=cms.InputTag("prunedGenParticles"),
    matchToGen=cms.bool(True),
    matchDR=cms.double(0.4),
    isData=cms.bool(isData),
    jetJECUncName=cms.FileInPath(
        "hep-poet/PhysObjectExtractor/JEC/Fall15_25nsV2_MC_Uncertainty_AK4PFchs.txt"
    ),
    jerResName=cms.FileInPath(
        "hep-poet/PhysObjectExtractor/JEC/Fall15_25nsV2_MC_PtResolution_AK4PFchs.txt"
    ),
    jerSFName=cms.FileInPath(
        "hep-poet/PhysObjectExtractor/JEC/Fall15_25nsV2_MC_SF_AK4PFchs.txt"
    ),
)
process.myfatjets = cms.EDAnalyzer(
    "FatjetAnalyzer",
    fatjets=cms.InputTag("slimmedJetsAK8NewJEC"),
    isData=cms.bool(isData),
    jecL2Name=cms.FileInPath(
        "hep-poet/PhysObjectExtractor/JEC/Fall15_25nsV2_"
        + JecString
        + "_L2Relative_AK8PFchs.txt"
    ),
    jecL3Name=cms.FileInPath(
        "hep-poet/PhysObjectExtractor/JEC/Fall15_25nsV2_"
        + JecString
        + "_L3Absolute_AK8PFchs.txt"
    ),
    jecResName=cms.FileInPath(
        "hep-poet/PhysObjectExtractor/JEC/Fall15_25nsV2_DATA_L2L3Residual_AK8PFchs.txt"
    ),
    jetJECUncName=cms.FileInPath(
        "hep-poet/PhysObjectExtractor/JEC/Fall15_25nsV2_MC_Uncertainty_AK8PFchs.txt"
    ),
    jerResName=cms.FileInPath(
        "hep-poet/PhysObjectExtractor/JEC/Fall15_25nsV2_MC_PtResolution_AK8PFchs.txt"
    ),
    jerSFName=cms.FileInPath(
        "hep-poet/PhysObjectExtractor/JEC/Fall15_25nsV2_MC_SF_AK4PFchs.txt"
    ),  # AK8 == AK4
)

# ----- Propagate the jet energy corrections to the MET -----#
from PhysicsTools.PatAlgos.tools.metTools import addMETCollection
from PhysicsTools.PatUtils.patPFMETCorrections_cff import patPFMetT1T2Corr

process.uncorrectedMet = cms.EDProducer(
    "RecoMETExtractor",
    correctionLevel=cms.string("raw"),
    metSource=cms.InputTag("slimmedMETs", "", "@skipCurrentProcess"),
)

addMETCollection(process, labelName="uncorrectedPatMet", metSource="uncorrectedMet")
process.uncorrectedPatMet.addGenMET = False

# ----- Evaluate the Type-1 correction -----#

process.Type1CorrForNewJEC = patPFMetT1T2Corr.clone(
    isMC=cms.bool(isMC),
    src=cms.InputTag("slimmedJetsNewJEC"),
)
process.slimmedMETsNewJEC = cms.EDProducer(
    "CorrectedPATMETProducer",
    src=cms.InputTag("uncorrectedPatMet"),
    srcCorrections=cms.VInputTag(cms.InputTag("Type1CorrForNewJEC", "type1")),
)

# ----- Configure the POET MET analyzer -----#
process.mymets = cms.EDAnalyzer(
    "MetAnalyzer",
    mets=cms.InputTag("slimmedMETsNewJEC"),
    rawmets=cms.InputTag("uncorrectedPatMet"),
)

process.mytriggers = cms.EDAnalyzer(
    "TriggerAnalyzer",
    processName=cms.string("HLT"),
    # ---- These are example triggers for 2012
    # ---- Wildcards * and ? are accepted (with usual meanings)
    # ---- If left empty, all triggers will run
    triggerPatterns=cms.vstring(
        "HLT_L2DoubleMu23_NoVertex_v*",
        "HLT_Mu12_v*",
        "HLT_Photon20_CaloIdVL_v*",
        "HLT_Ele22_CaloIdL_CaloIsoVL_v*",
        "HLT_Jet370_NoJetID_v*",
    ),
    triggerResults=cms.InputTag("TriggerResults", "", "HLT"),
    triggerEvent=cms.InputTag("hltTriggerSummaryAOD", "", "HLT"),
)
process.mypackedcandidate = cms.EDAnalyzer(
    "PackedCandidateAnalyzer", packed=cms.InputTag("packedPFCandidates")
)

# ---- Example of a very basic home-made filter to select only events of interest
# ---- The filter can be added to the running path below if needed
# ---- by uncommenting the lines below, but it is not applied by default
# process.elemufilter = cms.EDFilter('SimpleEleMuFilter',
#                                   electrons = cms.InputTag("slimmedElectrons"),
#                                   muons = cms.InputTag("slimmedMuons"),
#                                   vertices=cms.InputTag("offlineSlimmedPrimaryVertices"),
#                                   mu_minpt = cms.double(26),
#                                   mu_etacut = cms.double(2.1),
#                                   ele_minpt = cms.double(26),
#                                   ele_etacut = cms.double(2.1)
#                                   )


# ----- RUN THE JOB! -----#
process.TFileService = cms.Service(
    "TFileService",
    fileName=cms.string("test_ttbar_and_dm.root"),
)

if isData:
    process.p = cms.Path(
        process.myelectrons
        + process.mymuons
        + process.mypvertex
        + process.looseAK4Jets
        + process.patJetCorrFactorsReapplyJEC
        + process.slimmedJetsNewJEC
        + process.myjets
        + process.looseAK8Jets
        + process.patJetCorrFactorsReapplyJECAK8
        + process.slimmedJetsAK8NewJEC
        + process.myfatjets
        + process.uncorrectedMet
        + process.uncorrectedPatMet
        + process.Type1CorrForNewJEC
        + process.slimmedMETsNewJEC
        + process.mymets
    )
else:
    process.p = cms.Path(
        process.myelectrons
        + process.mymuons
        + process.mypvertex
        + process.mygenparticle
        + process.looseAK4Jets
        + process.patJetCorrFactorsReapplyJEC
        + process.slimmedJetsNewJEC
        + process.myjets
        + process.looseAK8Jets
        + process.patJetCorrFactorsReapplyJECAK8
        + process.slimmedJetsAK8NewJEC
        + process.myfatjets
        + process.uncorrectedMet
        + process.uncorrectedPatMet
        + process.Type1CorrForNewJEC
        + process.slimmedMETsNewJEC
        + process.mymets
    )
process.maxEvents.input = options.maxEvents
process.TFileService.fileName = options.outputFile
if len(options.inputFiles) > 0:
    process.source.fileNames = options.inputFiles

print("Processing for maxEvents =  ", process.maxEvents.input)
print("Processing input files ")
for fl in process.source.fileNames:
    print("  > ", fl)
print("Output filename : ", process.TFileService.fileName)
