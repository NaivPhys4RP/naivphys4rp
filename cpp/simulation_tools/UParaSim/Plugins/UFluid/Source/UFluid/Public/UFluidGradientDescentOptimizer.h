#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "UFluidSample.h"
#include "UFluidSmartSource.h"
#include "UFluidGradientDescentOptimizer.generated.h"

USTRUCT(BlueprintType)
struct FFluidParameterConfig
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    bool bIsEnabled = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float Epsilon = 0.01f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float LearningRate = 0.01f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float Beta1 = 0.9f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float Beta2 = 0.999f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float AdamEpsilon = 1e-8f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float LowerBound = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float UpperBound = 10.0f;

    float CachedBaseValue = 0.0f;

    // Adam optimizer internal tracking state
    float M = 0.0f;
    float V = 0.0f;
    int32 AdamStep = 0;
};

USTRUCT(BlueprintType)
struct FFluidSupervisionConfig
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    bool bIsEnabled = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float WeightFactor = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float NormalizationMax = 1.0f;
};

USTRUCT(BlueprintType)
struct FFluidMultivariateRecord
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere) int32 Iteration = 0;
    UPROPERTY(VisibleAnywhere) float TotalError = 0.0f;

    // --- 1. Learned Parameters (Inputs) ---
    UPROPERTY(VisibleAnywhere) float ParamScale = 0.0f;
    UPROPERTY(VisibleAnywhere) float ParamDensity = 0.0f;
    UPROPERTY(VisibleAnywhere) float ParamFriction = 0.0f;
    UPROPERTY(VisibleAnywhere) float ParamRestitution = 0.0f;
    UPROPERTY(VisibleAnywhere) float ParamDestructibility = 0.0f;
    UPROPERTY(VisibleAnywhere) float ParamAngularDamping = 0.0f;
    UPROPERTY(VisibleAnywhere) float ParamLinearDamping = 0.0f;
    UPROPERTY(VisibleAnywhere) float ParamCovalentBondLength = 0.0f;
    UPROPERTY(VisibleAnywhere) float ParamCovalentBondForce = 0.0f;
    UPROPERTY(VisibleAnywhere) float ParamBondThickness = 0.0f;

    // --- 2. Expected Supervision Values (Targets) ---
    UPROPERTY(VisibleAnywhere) float Target_FlowTime = 0.0f;
    UPROPERTY(VisibleAnywhere) float Target_SpreadArea = 0.0f;
    UPROPERTY(VisibleAnywhere) float Target_Spillage = 0.0f;
    UPROPERTY(VisibleAnywhere) float Target_Overflow = 0.0f;
    UPROPERTY(VisibleAnywhere) float Target_Volume = 0.0f;
    UPROPERTY(VisibleAnywhere) float Target_TipOver = 0.0f;
    UPROPERTY(VisibleAnywhere) float Target_Occupancy = 0.0f;

    // --- 3. Actual Supervision Values (Observed Outputs) ---
    UPROPERTY(VisibleAnywhere) float Observed_FlowTime = 0.0f;
    UPROPERTY(VisibleAnywhere) float Observed_SpreadArea = 0.0f;
    UPROPERTY(VisibleAnywhere) float Observed_Spillage = 0.0f;
    UPROPERTY(VisibleAnywhere) float Observed_Overflow = 0.0f;
    UPROPERTY(VisibleAnywhere) float Observed_Volume = 0.0f;
    UPROPERTY(VisibleAnywhere) float Observed_TipOver = 0.0f;
    UPROPERTY(VisibleAnywhere) float Observed_Occupancy = 0.0f;

    // --- 4. Individual Normalized Errors (Loss Components) ---
    UPROPERTY(VisibleAnywhere) float Error_FlowTime = 0.0f;
    UPROPERTY(VisibleAnywhere) float Error_SpreadArea = 0.0f;
    UPROPERTY(VisibleAnywhere) float Error_Spillage = 0.0f;
    UPROPERTY(VisibleAnywhere) float Error_Overflow = 0.0f;
    UPROPERTY(VisibleAnywhere) float Error_Volume = 0.0f;
    UPROPERTY(VisibleAnywhere) float Error_TipOver = 0.0f;
    UPROPERTY(VisibleAnywhere) float Error_Occupancy = 0.0f;
};

UENUM()
enum class EMultiOptimizerState : uint8
{
    IDLE,
    EVALUATING_BASE,
    EVALUATING_PERTURBATIONS
};

UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class UFLUID_API UFluidGradientDescentOptimizer : public UActorComponent
{
    GENERATED_BODY()

public:
    UFluidGradientDescentOptimizer();

protected:
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

public:

    UPROPERTY()
    float InitialDeltaPosition = 1.0f;

    UPROPERTY()
    float InitialDeltaOrientation = 1.0f;

    UPROPERTY()
    float InitialTargetTiltDelta = 0.0f;

    UPROPERTY()
    float InitialTargetMoveVerticalDelta = 0.0f;

    UPROPERTY()
    float InitialTargetMoveHorizontalDelta = 0.0f;

    UPROPERTY(EditAnywhere, Category = "Optimizer | Configuration")
    AUFluidSample* FluidSampleActor = nullptr;

    UPROPERTY(EditAnywhere, Category = "Optimizer | Configuration")
    AUFluidSmartSource* FunnelActor = nullptr;

    UPROPERTY(EditAnywhere, Category = "Optimizer | Hyperparameters")
    bool OptimizationEnabled = false;

    // Add these to your UFluidGradientDescentOptimizer class properties in the header (.h)
    UPROPERTY(EditAnywhere, Category = "Optimizer | Manipulation")
    float TargetTiltDelta = 0.0f;

    UPROPERTY(EditAnywhere, Category = "Optimizer | Manipulation")
    float TargetMoveVerticalDelta = 0.0f;

    UPROPERTY(EditAnywhere, Category = "Optimizer | Manipulation")
    float TargetMoveHorizontalDelta = 0.0f;

    // --- 10 Configurable Fluid Physical Parameters ---
    UPROPERTY(EditAnywhere, Category = "Optimizer | Fluid Parameter Spaces") FFluidParameterConfig ParamScale;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Fluid Parameter Spaces") FFluidParameterConfig ParamDensity;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Fluid Parameter Spaces") FFluidParameterConfig ParamFriction;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Fluid Parameter Spaces") FFluidParameterConfig ParamRestitution;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Fluid Parameter Spaces") FFluidParameterConfig ParamDestructibility;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Fluid Parameter Spaces") FFluidParameterConfig ParamAngularDamping;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Fluid Parameter Spaces") FFluidParameterConfig ParamLinearDamping;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Fluid Parameter Spaces") FFluidParameterConfig ParamCovalentBondLength;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Fluid Parameter Spaces") FFluidParameterConfig ParamCovalentBondForce;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Fluid Parameter Spaces") FFluidParameterConfig ParamBondThickness;

    // --- 7 Supervision Signals & Targets ---
    UPROPERTY(EditAnywhere, Category = "Optimizer | Supervision | Flow Time") FFluidSupervisionConfig SignalFlowTime;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Supervision | Flow Time") float TargetFlowingTime = 5.4f;

    UPROPERTY(EditAnywhere, Category = "Optimizer | Supervision | Spread Area") FFluidSupervisionConfig SignalSpreadArea;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Supervision | Spread Area") float TargetSpreadArea = 1200.0f;

    UPROPERTY(EditAnywhere, Category = "Optimizer | Supervision | Spillage") FFluidSupervisionConfig SignalSpillage;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Supervision | Spillage") float TargetSpillage = 0.0f;

    UPROPERTY(EditAnywhere, Category = "Optimizer | Supervision | Overflow") FFluidSupervisionConfig SignalOverflow;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Supervision | Overflow") float TargetOverflow = 0.0f;

    UPROPERTY(EditAnywhere, Category = "Optimizer | Supervision | Volume") FFluidSupervisionConfig SignalVolume;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Supervision | Volume") float TargetVolume = 500.0f;

    UPROPERTY(EditAnywhere, Category = "Optimizer | Supervision | TipOver") FFluidSupervisionConfig SignalTipOver;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Supervision | TipOver") float TargetTipOver = 0.0f;

    UPROPERTY(EditAnywhere, Category = "Optimizer | Supervision | Occupancy") FFluidSupervisionConfig SignalOccupancy;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Supervision | Occupancy") float TargetOccupancy = 0.8f;

    // --- Simulation Core Boundaries ---
    UPROPERTY(EditAnywhere, Category = "Optimizer | Safety") float MaxSimTime = 25.0f;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Safety") float MaxSettlingTime = 10.0f;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Safety") float InfinityPenalty = 1.0f;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Safety") float ThresholdPercent = 90.0f;
    UPROPERTY(EditAnywhere, Category = "Optimizer | Safety") float ThresholdDistance = 50.0f;

    // --- CSV Trajectory Tracker ---
    UPROPERTY(EditAnywhere, Category = "Optimizer | Export") FString ExportFileName = TEXT("multivariate_history");
    UPROPERTY(VisibleAnywhere, Category = "Optimizer | History") TArray<FFluidMultivariateRecord> History;

    UFUNCTION(BlueprintCallable, CallInEditor, Category = "Optimizer | History")
    void ExportHistoryToCSV();

private:
    EMultiOptimizerState CurrentState = EMultiOptimizerState::IDLE;
    int32 IterationCounter = 0;
    int32 CurrentPerturbationIndex = 0;

    TArray<FFluidParameterConfig*> ActiveParamPointers;
    TArray<FString> ActiveParamNames;

    FTransform InitialFluidTransform;
    FTransform InitialMainContainerTransform;
    FTransform InitialDestinationContainerTransform;
    int32 InitialParticleStock;
    float EffectiveFlowTime;
    float BaseError;
    float StagnationTimer;
    float SettlingTimer;
    float LastEscapedPercent;

    FFluidMultivariateRecord CachedBaseRecord;

    void RestartSimulation();
    void SetupParameterSequencer();

    float GetParameterValueByIndex(int32 Index);
    void SetParameterValueByIndex(int32 Index, float Value);
    void SyncActorParametersWithConfigs();

    float CalculateCurrentNormalizedError(bool bClogged, FFluidMultivariateRecord& OutRecordData);

    // Virtual telemetry accessors
    float ComputeSpillage();
    float ComputeOverflow();
    float ComputeVolume();
    float ComputeTipOver();
    float ComputeOccupancy();
    float ComputeFlowTime();
    float ComputeSpreadArea(float ThresholdPercent, float ThresholdDistance);

    //Manipulation function as part of the function execution
    bool Manipulation();
};
