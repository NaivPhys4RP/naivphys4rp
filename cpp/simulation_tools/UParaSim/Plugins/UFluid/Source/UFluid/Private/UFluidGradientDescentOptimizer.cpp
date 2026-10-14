#include "UFluidGradientDescentOptimizer.h"
#include "UFluidEmitter.h"
#include "UFluidParticle.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

UFluidGradientDescentOptimizer::UFluidGradientDescentOptimizer()
{
    PrimaryComponentTick.bCanEverTick = true;

    // Default search space parameter controls, individual learning rates, and perturbation epsilons (10 Parameters)
    ParamScale.LowerBound = 0.001f;                 ParamScale.UpperBound = 0.05f;               ParamScale.Epsilon = 0.0005f; ParamScale.LearningRate = 0.001f;
    ParamDensity.LowerBound = 1.0f;                 ParamDensity.UpperBound = 2000.0f;           ParamDensity.Epsilon = 10.0f; ParamDensity.LearningRate = 0.1f;
    ParamFriction.LowerBound = 0.0f;                ParamFriction.UpperBound = 1.0f;             ParamFriction.Epsilon = 0.05f; ParamFriction.LearningRate = 0.01f;
    ParamRestitution.LowerBound = 0.0f;             ParamRestitution.UpperBound = 1.0f;          ParamRestitution.Epsilon = 0.05f; ParamRestitution.LearningRate = 0.01f;
    ParamDestructibility.LowerBound = 0.0f;         ParamDestructibility.UpperBound = 1.0f;      ParamDestructibility.Epsilon = 0.05f; ParamDestructibility.LearningRate = 0.01f;
    ParamAngularDamping.LowerBound = 0.0f;          ParamAngularDamping.UpperBound = 50.0f;      ParamAngularDamping.Epsilon = 1.0f; ParamAngularDamping.LearningRate = 0.01f;
    ParamLinearDamping.LowerBound = 0.0f;           ParamLinearDamping.UpperBound = 50.0f;       ParamLinearDamping.Epsilon = 1.0f; ParamLinearDamping.LearningRate = 0.01f;
    ParamCovalentBondLength.LowerBound = 0.0f;      ParamCovalentBondLength.UpperBound = 100.0f; ParamCovalentBondLength.Epsilon = 2.0f; ParamCovalentBondLength.LearningRate = 0.1f;
    ParamCovalentBondForce.LowerBound = 0.0f;       ParamCovalentBondForce.UpperBound = 100.0f;  ParamCovalentBondForce.Epsilon = 2.0f; ParamCovalentBondForce.LearningRate = 0.1f;
    ParamBondThickness.LowerBound = 0.0f;           ParamBondThickness.UpperBound = 10.0f;       ParamBondThickness.Epsilon = 0.1f; ParamBondThickness.LearningRate = 0.01f;

    // Normalization maximum boundaries
    SignalFlowTime.NormalizationMax = 25.0f;
    SignalSpreadArea.NormalizationMax = 5000.0f;
    SignalVolume.NormalizationMax = 2000.0f;
    SignalSpillage.NormalizationMax = 1.0f;
    SignalOverflow.NormalizationMax = 1.0f;
    SignalTipOver.NormalizationMax = 1.0f;
    SignalOccupancy.NormalizationMax = 1.0f;
}

void UFluidGradientDescentOptimizer::BeginPlay()
{
    Super::BeginPlay();

    PrimaryComponentTick.SetTickFunctionEnable(true);

    if (!FluidSampleActor)
    {
        UE_LOG(LogTemp, Error, TEXT("Fluid Optimizer: FluidSampleActor is NULL in BeginPlay!"));
        return;
    }

    if (!FluidSampleActor->U_FluidEmitter)
    {
        UE_LOG(LogTemp, Warning, TEXT("Fluid Optimizer: U_FluidEmitter is null during BeginPlay. Retrying or waiting for initialization..."));
    }
    else
    {
        InitialFluidTransform = FluidSampleActor->GetActorTransform();
        if (FluidSampleActor->U_FluidMainContainer)
        {
            InitialMainContainerTransform = FluidSampleActor->U_FluidMainContainer->GetActorTransform();
            // When initializing your experiment or reading user configuration
            InitialTargetTiltDelta = TargetTiltDelta;
            InitialTargetMoveVerticalDelta = TargetMoveVerticalDelta;
            InitialTargetMoveHorizontalDelta = TargetMoveHorizontalDelta;

            InitialDeltaPosition = FluidSampleActor->U_FluidMainContainer->Delta_Position;
            InitialDeltaOrientation = FluidSampleActor->U_FluidMainContainer->Delta_Orientation;
        }
        if (FluidSampleActor->U_FluidDestinationContainer)
        {
            InitialDestinationContainerTransform = FluidSampleActor->U_FluidDestinationContainer->GetActorTransform();
        }
        InitialParticleStock = FluidSampleActor->U_FluidEmitter->U_NumberParticles;
        IterationCounter = 0;
        SetupParameterSequencer();
        CurrentState = EMultiOptimizerState::EVALUATING_BASE;

        RestartSimulation();
        UE_LOG(LogTemp, Warning, TEXT("Fluid Optimizer: Successfully initialized and kicked off simulation in BeginPlay!"));
    }
}

void UFluidGradientDescentOptimizer::SetupParameterSequencer()
{
    ActiveParamPointers.Empty();
    ActiveParamNames.Empty();

    if (ParamScale.bIsEnabled)                 { ActiveParamPointers.Add(&ParamScale);                 ActiveParamNames.Add(TEXT("Scale")); }
    if (ParamDensity.bIsEnabled)               { ActiveParamPointers.Add(&ParamDensity);               ActiveParamNames.Add(TEXT("Density")); }
    if (ParamFriction.bIsEnabled)              { ActiveParamPointers.Add(&ParamFriction);              ActiveParamNames.Add(TEXT("Friction")); }
    if (ParamRestitution.bIsEnabled)           { ActiveParamPointers.Add(&ParamRestitution);           ActiveParamNames.Add(TEXT("Restitution")); }
    if (ParamDestructibility.bIsEnabled)       { ActiveParamPointers.Add(&ParamDestructibility);       ActiveParamNames.Add(TEXT("Destructibility")); }
    if (ParamAngularDamping.bIsEnabled)        { ActiveParamPointers.Add(&ParamAngularDamping);        ActiveParamNames.Add(TEXT("AngularDamping")); }
    if (ParamLinearDamping.bIsEnabled)         { ActiveParamPointers.Add(&ParamLinearDamping);         ActiveParamNames.Add(TEXT("LinearDamping")); }
    if (ParamCovalentBondLength.bIsEnabled)    { ActiveParamPointers.Add(&ParamCovalentBondLength);    ActiveParamNames.Add(TEXT("CovalentBondLength")); }
    if (ParamCovalentBondForce.bIsEnabled)     { ActiveParamPointers.Add(&ParamCovalentBondForce);     ActiveParamNames.Add(TEXT("CovalentBondForce")); }
    if (ParamBondThickness.bIsEnabled)         { ActiveParamPointers.Add(&ParamBondThickness);         ActiveParamNames.Add(TEXT("BondThickness")); }
}

float UFluidGradientDescentOptimizer::GetParameterValueByIndex(int32 Index)
{
    if (!ActiveParamNames.IsValidIndex(Index)) return 0.0f;
    FString Name = ActiveParamNames[Index];
    if (Name == TEXT("Scale"))                 return FluidSampleActor->U_ParticleScale.X;
    if (Name == TEXT("Density"))               return FluidSampleActor->U_FluidDensity;
    if (Name == TEXT("Friction"))              return FluidSampleActor->U_FluidFriction;
    if (Name == TEXT("Restitution"))           return FluidSampleActor->U_FluidRestitution;
    if (Name == TEXT("Destructibility"))       return FluidSampleActor->U_FluidDestructibility;
    if (Name == TEXT("AngularDamping"))        return FluidSampleActor->U_FluidAngularDamping;
    if (Name == TEXT("LinearDamping"))         return FluidSampleActor->U_FluidLinearDamping;
    if (Name == TEXT("CovalentBondLength"))    return FluidSampleActor->U_CovalentBond;
    if (Name == TEXT("CovalentBondForce"))     return FluidSampleActor->U_CovalentBondForce;
    if (Name == TEXT("BondThickness"))         return FluidSampleActor->U_CovalentBondTickness;
    return 0.0f;
}

void UFluidGradientDescentOptimizer::SetParameterValueByIndex(int32 Index, float Value)
{
    if (!ActiveParamNames.IsValidIndex(Index)) return;
    FString Name = ActiveParamNames[Index];
    if (Name == TEXT("Scale"))                 FluidSampleActor->U_ParticleScale = FVector(Value);
    if (Name == TEXT("Density"))               FluidSampleActor->U_FluidDensity = Value;
    if (Name == TEXT("Friction"))              FluidSampleActor->U_FluidFriction = Value;
    if (Name == TEXT("Restitution"))           FluidSampleActor->U_FluidRestitution = Value;
    if (Name == TEXT("Destructibility"))       FluidSampleActor->U_FluidDestructibility = Value;
    if (Name == TEXT("AngularDamping"))        FluidSampleActor->U_FluidAngularDamping = Value;
    if (Name == TEXT("LinearDamping"))         FluidSampleActor->U_FluidLinearDamping = Value;
    if (Name == TEXT("CovalentBondLength"))    FluidSampleActor->U_CovalentBond = Value;
    if (Name == TEXT("CovalentBondForce"))     FluidSampleActor->U_CovalentBondForce = Value;
    if (Name == TEXT("BondThickness"))         FluidSampleActor->U_CovalentBondTickness = Value;
}

void UFluidGradientDescentOptimizer::SyncActorParametersWithConfigs()
{
    FluidSampleActor->U_ParticleScale = FVector(ParamScale.CachedBaseValue);
    FluidSampleActor->U_FluidDensity = ParamDensity.CachedBaseValue;
    FluidSampleActor->U_FluidFriction = ParamFriction.CachedBaseValue;
    FluidSampleActor->U_FluidRestitution = ParamRestitution.CachedBaseValue;
    FluidSampleActor->U_FluidDestructibility = ParamDestructibility.CachedBaseValue;
    FluidSampleActor->U_FluidAngularDamping = ParamAngularDamping.CachedBaseValue;
    FluidSampleActor->U_FluidLinearDamping = ParamLinearDamping.CachedBaseValue;
    FluidSampleActor->U_CovalentBond = ParamCovalentBondLength.CachedBaseValue;
    FluidSampleActor->U_CovalentBondForce = ParamCovalentBondForce.CachedBaseValue;
    FluidSampleActor->U_CovalentBondTickness = ParamBondThickness.CachedBaseValue;
}

float UFluidGradientDescentOptimizer::CalculateCurrentNormalizedError(bool bClogged, FFluidMultivariateRecord& OutRecordData)
{
    if (bClogged) return InfinityPenalty;

    float AccumulatorLoss = 0.0f;

    // --- Write Expected Values (Targets) ---
    OutRecordData.Target_FlowTime   = TargetFlowingTime;
    OutRecordData.Target_SpreadArea = TargetSpreadArea;
    OutRecordData.Target_Spillage   = TargetSpillage;
    OutRecordData.Target_Overflow   = TargetOverflow;
    OutRecordData.Target_Volume     = TargetVolume;
    OutRecordData.Target_TipOver    = TargetTipOver;
    OutRecordData.Target_Occupancy  = TargetOccupancy;

    // --- Write Observed Values (Outputs) & Calculate Errors (Losses) ---

    // 1. Flow Time
    OutRecordData.Observed_FlowTime = EffectiveFlowTime;
    if (SignalFlowTime.bIsEnabled)
    {
        float RawErr = FMath::Abs(TargetFlowingTime - this->ComputeFlowTime());
        OutRecordData.Error_FlowTime = FMath::Square(RawErr / SignalFlowTime.NormalizationMax) * SignalFlowTime.WeightFactor;
        AccumulatorLoss += OutRecordData.Error_FlowTime;
    }
    else { OutRecordData.Error_FlowTime = 0.0f; }

    // 2. Spread Area
    OutRecordData.Observed_SpreadArea = this->ComputeSpreadArea(this->ThresholdPercent, this->ThresholdDistance);
    if (SignalSpreadArea.bIsEnabled)
    {
        float RawErr = FMath::Abs(TargetSpreadArea - OutRecordData.Observed_SpreadArea);
        OutRecordData.Error_SpreadArea = FMath::Square(RawErr / SignalSpreadArea.NormalizationMax) * SignalSpreadArea.WeightFactor;
        AccumulatorLoss += OutRecordData.Error_SpreadArea;
    }
    else { OutRecordData.Error_SpreadArea = 0.0f; }

    // 3. Spillage
    OutRecordData.Observed_Spillage = ComputeSpillage();
    if (SignalSpillage.bIsEnabled)
    {
        float Target = TargetSpillage;
        float Predicted = FMath::Clamp(OutRecordData.Observed_Spillage, 1e-7f, 1.0f - 1e-7f);

        // Binary Cross-Entropy Loss
        float BCE = - (Target * FMath::Loge(Predicted) + (1.0f - Target) * FMath::Loge(1.0f - Predicted));

        OutRecordData.Error_Spillage = BCE * SignalSpillage.WeightFactor;
        AccumulatorLoss += OutRecordData.Error_Spillage;
    }
    else { OutRecordData.Error_Spillage = 0.0f; }


    // 4. Overflow
    OutRecordData.Observed_Overflow = ComputeOverflow();
    if (SignalOverflow.bIsEnabled)
    {
        float Target = TargetOverflow;
        float Predicted = FMath::Clamp(OutRecordData.Observed_Overflow, 1e-7f, 1.0f - 1e-7f);

        // Binary Cross-Entropy Loss
        float BCE = - (Target * FMath::Loge(Predicted) + (1.0f - Target) * FMath::Loge(1.0f - Predicted));

        OutRecordData.Error_Overflow = BCE * SignalOverflow.WeightFactor;
        AccumulatorLoss += OutRecordData.Error_Overflow;
    }
    else { OutRecordData.Error_Overflow = 0.0f; }

    // 5. Volume
    OutRecordData.Observed_Volume = ComputeVolume();
    if (SignalVolume.bIsEnabled)
    {
        OutRecordData.Error_Volume = FMath::Square(FMath::Abs(TargetVolume - OutRecordData.Observed_Volume) / SignalVolume.NormalizationMax) * SignalVolume.WeightFactor;
        AccumulatorLoss += OutRecordData.Error_Volume;
    }
    else { OutRecordData.Error_Volume = 0.0f; }

    // 6. TipOver
    OutRecordData.Observed_TipOver = ComputeTipOver();
    if (SignalTipOver.bIsEnabled)
    {
        float Target = TargetTipOver;
        float Predicted = FMath::Clamp(OutRecordData.Observed_TipOver, 1e-7f, 1.0f - 1e-7f);

        // Binary Cross-Entropy Loss
        float BCE = - (Target * FMath::Loge(Predicted) + (1.0f - Target) * FMath::Loge(1.0f - Predicted));

        OutRecordData.Error_TipOver = BCE * SignalTipOver.WeightFactor;
        AccumulatorLoss += OutRecordData.Error_TipOver;
    }
    else { OutRecordData.Error_TipOver = 0.0f; }

    // 7. Occupancy
    OutRecordData.Observed_Occupancy = ComputeOccupancy();

    if (SignalOccupancy.bIsEnabled)
    {
        OutRecordData.Error_Occupancy = FMath::Square(FMath::Abs(TargetOccupancy - OutRecordData.Observed_Occupancy) / SignalOccupancy.NormalizationMax) * SignalOccupancy.WeightFactor;
        AccumulatorLoss += OutRecordData.Error_Occupancy;
    }
    else { OutRecordData.Error_Occupancy = 0.0f; }

    return AccumulatorLoss;
}

void UFluidGradientDescentOptimizer::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!this->OptimizationEnabled)
    {
        return;
    }

    if (!FluidSampleActor)
    {
        UE_LOG(LogTemp, Error, TEXT("Optimizer skipped: FluidSampleActor is NULL!"));
        return;
    }

    if (!FluidSampleActor->U_FluidEmitter)
    {
        UE_LOG(LogTemp, Error, TEXT("Optimizer skipped: U_FluidEmitter is NULL!"));
        return;
    }

    if (CurrentState == EMultiOptimizerState::IDLE)
    {
        UE_LOG(LogTemp, Warning, TEXT("Optimizer skipped: CurrentState is stuck in IDLE!"));
        if (FluidSampleActor && FluidSampleActor->U_FluidEmitter)
        {
            InitialFluidTransform = FluidSampleActor->GetActorTransform();
            if (FluidSampleActor->U_FluidMainContainer)
            {
                InitialMainContainerTransform = FluidSampleActor->U_FluidMainContainer->GetActorTransform();
                // When initializing your experiment or reading user configuration
                InitialTargetTiltDelta = TargetTiltDelta;
                InitialTargetMoveVerticalDelta = TargetMoveVerticalDelta;
                InitialTargetMoveHorizontalDelta = TargetMoveHorizontalDelta;

                InitialDeltaPosition = FluidSampleActor->U_FluidMainContainer->Delta_Position;
                InitialDeltaOrientation = FluidSampleActor->U_FluidMainContainer->Delta_Orientation;
            }
            if (FluidSampleActor->U_FluidDestinationContainer)
            {
                InitialDestinationContainerTransform = FluidSampleActor->U_FluidDestinationContainer->GetActorTransform();
            }

            InitialParticleStock = FluidSampleActor->U_FluidEmitter->U_NumberParticles;
            IterationCounter = 0;
            SetupParameterSequencer();
            CurrentState = EMultiOptimizerState::EVALUATING_BASE;

            RestartSimulation();
            UE_LOG(LogTemp, Warning, TEXT("Fluid Optimizer: Successfully recovered and initialized from Tick! Starting base evaluation."));
        }
        else
        {
            return;
        }
    }

    // Determine Mode: Funnel vs Pouring
    // Funnel mode if either Area or FlowTime flags are on (default case)
    bool bIsPouringMode = (SignalSpillage.bIsEnabled || SignalOverflow.bIsEnabled || SignalVolume.bIsEnabled || SignalTipOver.bIsEnabled);

    // Handle Pouring Mode specific timing & manipulation sequence
    if (bIsPouringMode)
    {
        // Track time since restart for triggering manipulation delay
        EffectiveFlowTime += DeltaTime;

        // Trigger manipulation a few seconds after restart (e.g., 5.0 seconds delay)
        float ManipulationDelay = 5.0f;
        if (EffectiveFlowTime >= ManipulationDelay)
        {
            // Call manipulation; keeps executing step-by-step until it returns false (finished)
            bool bManipulationActive = Manipulation();
            if (!bManipulationActive)
            {
                // Once manipulation finishes, accumulate settling time
                SettlingTimer += DeltaTime;
            }
        }
    }
    else
    {
        // Default Funnel Mode tracking logic
        float CurrentEscaped = FluidSampleActor->QUANTITY_ESCAPED;
        bool bAllEscaped = (CurrentEscaped >= 100.0f);
        bool bHasStartedEscaping = (CurrentEscaped > 0.0f);

        if (bHasStartedEscaping && !bAllEscaped)
        {
            EffectiveFlowTime += DeltaTime;
            if (FMath::IsNearlyEqual(CurrentEscaped, LastEscapedPercent, 0.001f)) StagnationTimer += DeltaTime;
            else StagnationTimer = 0.0f;
        }
        LastEscapedPercent = CurrentEscaped;

        if (bAllEscaped) SettlingTimer += DeltaTime;
    }

    bool bClogged = (!bIsPouringMode && StagnationTimer > MaxSimTime && FluidSampleActor->QUANTITY_ESCAPED < 100.0f);
    bool bTimedOut = (EffectiveFlowTime > MaxSimTime);

    // Termination condition check based on mode
    bool bFinishedAndSettled = bIsPouringMode
        ? (SettlingTimer >= this->MaxSettlingTime)
        : ((FluidSampleActor->QUANTITY_ESCAPED >= 100.0f) && SettlingTimer >= this->MaxSettlingTime);

    if (bFinishedAndSettled || bClogged || bTimedOut)
    {
        SetupParameterSequencer();
        if (ActiveParamPointers.Num() == 0) return;

        if (CurrentState == EMultiOptimizerState::EVALUATING_BASE)
        {
            ParamScale.CachedBaseValue              = FluidSampleActor->U_ParticleScale.X;
            ParamDensity.CachedBaseValue            = FluidSampleActor->U_FluidDensity;
            ParamFriction.CachedBaseValue           = FluidSampleActor->U_FluidFriction;
            ParamRestitution.CachedBaseValue        = FluidSampleActor->U_FluidRestitution;
            ParamDestructibility.CachedBaseValue    = FluidSampleActor->U_FluidDestructibility;
            ParamAngularDamping.CachedBaseValue     = FluidSampleActor->U_FluidAngularDamping;
            ParamLinearDamping.CachedBaseValue      = FluidSampleActor->U_FluidLinearDamping;
            ParamCovalentBondLength.CachedBaseValue = FluidSampleActor->U_CovalentBond;
            ParamCovalentBondForce.CachedBaseValue  = FluidSampleActor->U_CovalentBondForce;
            ParamBondThickness.CachedBaseValue      = FluidSampleActor->U_CovalentBondTickness;

            BaseError = CalculateCurrentNormalizedError(bClogged || bTimedOut, CachedBaseRecord);

            CurrentPerturbationIndex = 0;
            CurrentState = EMultiOptimizerState::EVALUATING_PERTURBATIONS;

            float CurrentVal = GetParameterValueByIndex(CurrentPerturbationIndex);
            SetParameterValueByIndex(CurrentPerturbationIndex, CurrentVal + ActiveParamPointers[CurrentPerturbationIndex]->Epsilon);

            RestartSimulation();
        }
        else if (CurrentState == EMultiOptimizerState::EVALUATING_PERTURBATIONS)
        {
            FFluidMultivariateRecord PerturbedSnapshot;
            float PerturbedError = CalculateCurrentNormalizedError(bClogged || bTimedOut, PerturbedSnapshot);

            FFluidParameterConfig* Config = ActiveParamPointers[CurrentPerturbationIndex];
            float LocalEpsilon = Config->Epsilon;
            float Gradient = (PerturbedError - BaseError) / LocalEpsilon;

            // --- Adam Optimizer Update Step with Individual Parameters ---
            Config->AdamStep++;
            Config->M = Config->Beta1 * Config->M + (1.0f - Config->Beta1) * Gradient;
            Config->V = Config->Beta2 * Config->V + (1.0f - Config->Beta2) * (Gradient * Gradient);

            float BiasCorrection1 = 1.0f - FMath::Pow(Config->Beta1, (float)Config->AdamStep);
            float BiasCorrection2 = 1.0f - FMath::Pow(Config->Beta2, (float)Config->AdamStep);

            float MHat = Config->M / BiasCorrection1;
            float VHat = Config->V / BiasCorrection2;

            float OriginalValue = 0.0f;
            FString TargetName = ActiveParamNames[CurrentPerturbationIndex];
            if (TargetName == TEXT("Scale"))                 OriginalValue = ParamScale.CachedBaseValue;
            if (TargetName == TEXT("Density"))               OriginalValue = ParamDensity.CachedBaseValue;
            if (TargetName == TEXT("Friction"))              OriginalValue = ParamFriction.CachedBaseValue;
            if (TargetName == TEXT("Restitution"))           OriginalValue = ParamRestitution.CachedBaseValue;
            if (TargetName == TEXT("Destructibility"))       OriginalValue = ParamDestructibility.CachedBaseValue;
            if (TargetName == TEXT("AngularDamping"))        OriginalValue = ParamAngularDamping.CachedBaseValue;
            if (TargetName == TEXT("LinearDamping"))         OriginalValue = ParamLinearDamping.CachedBaseValue;
            if (TargetName == TEXT("CovalentBondLength"))    OriginalValue = ParamCovalentBondLength.CachedBaseValue;
            if (TargetName == TEXT("CovalentBondForce"))     OriginalValue = ParamCovalentBondForce.CachedBaseValue;
            if (TargetName == TEXT("BondThickness"))         OriginalValue = ParamBondThickness.CachedBaseValue;

            // Apply Adam update rule
            float NewValue = OriginalValue - Config->LearningRate * MHat / (FMath::Sqrt(VHat) + Config->AdamEpsilon);
            NewValue = FMath::Clamp(NewValue, Config->LowerBound, Config->UpperBound);

            Config->CachedBaseValue = NewValue;
            CurrentPerturbationIndex++;

            if (CurrentPerturbationIndex < ActiveParamPointers.Num())
            {
                SyncActorParametersWithConfigs();
                float NextVal = GetParameterValueByIndex(CurrentPerturbationIndex);
                SetParameterValueByIndex(CurrentPerturbationIndex, NextVal + ActiveParamPointers[CurrentPerturbationIndex]->Epsilon);
                RestartSimulation();
            }
            else
            {
                SyncActorParametersWithConfigs();

                CachedBaseRecord.Iteration = IterationCounter++;
                CachedBaseRecord.TotalError = BaseError;
                CachedBaseRecord.ParamScale = ParamScale.CachedBaseValue;
                CachedBaseRecord.ParamDensity = ParamDensity.CachedBaseValue;
                CachedBaseRecord.ParamFriction = ParamFriction.CachedBaseValue;
                CachedBaseRecord.ParamRestitution = ParamRestitution.CachedBaseValue;
                CachedBaseRecord.ParamDestructibility = ParamDestructibility.CachedBaseValue;
                CachedBaseRecord.ParamAngularDamping = ParamAngularDamping.CachedBaseValue;
                CachedBaseRecord.ParamLinearDamping = ParamLinearDamping.CachedBaseValue;
                CachedBaseRecord.ParamCovalentBondLength = ParamCovalentBondLength.CachedBaseValue;
                CachedBaseRecord.ParamCovalentBondForce = ParamCovalentBondForce.CachedBaseValue;
                CachedBaseRecord.ParamBondThickness = ParamBondThickness.CachedBaseValue;

                History.Add(CachedBaseRecord);

                CurrentState = EMultiOptimizerState::EVALUATING_BASE;
                RestartSimulation();
            }
        }
    }
}

void UFluidGradientDescentOptimizer::RestartSimulation()
{
    UUFluidEmitter* Emitter = FluidSampleActor->U_FluidEmitter;
    if (!Emitter) return;

    for (auto* P : Emitter->U_FluidParticles)
    {
        if (P) P->DeleteParticle();
    }
    Emitter->U_FluidParticles.Empty();

    EffectiveFlowTime = 0.0f;
    StagnationTimer = 0.0f;
    SettlingTimer = 0.0f;
    LastEscapedPercent = 0.0f;

    TargetTiltDelta = InitialTargetTiltDelta;
    TargetMoveVerticalDelta = InitialTargetMoveVerticalDelta;
    TargetMoveHorizontalDelta = InitialTargetMoveHorizontalDelta;

    FluidSampleActor->bIsSpilledFlag = 0.0f;
    FluidSampleActor->bIsOverflowFlag = 0.0f;
    FluidSampleActor->CachedTipOver = 0.0f;
    FluidSampleActor->CachedOccupancy = 0.0f;
    FluidSampleActor->CachedFlowTime = 0.0f;
    FluidSampleActor->CachedSpreadArea = 0.0f;
    FluidSampleActor->CachedTargetVolume = 0.0f;

    FluidSampleActor->QUANTITY_ESCAPED = 0.0f;
    FluidSampleActor->SetActorTransform(InitialFluidTransform);

    if (Emitter->U_ParticleModel)
    {
        Emitter->U_ParticleModel->Scale = FluidSampleActor->U_ParticleScale;
        Emitter->U_ParticleModel->Linear_Damping = FluidSampleActor->U_FluidLinearDamping;
        Emitter->U_ParticleModel->Density = FluidSampleActor->U_FluidDensity;
        Emitter->U_ParticleModel->Friction = FluidSampleActor->U_FluidFriction;
        Emitter->U_ParticleModel->Restitution = FluidSampleActor->U_FluidRestitution;
        Emitter->U_ParticleModel->Destructibility = FluidSampleActor->U_FluidDestructibility;
        Emitter->U_ParticleModel->Angular_Damping = FluidSampleActor->U_FluidAngularDamping;
    }

    Emitter->U_NumberParticles = InitialParticleStock;
    Emitter->U_IsPaused = false;
    if (FluidSampleActor)
    {
            FluidSampleActor->SetActorTransform(InitialFluidTransform);

            if (FluidSampleActor->U_FluidMainContainer)
            {
                FluidSampleActor->U_FluidMainContainer->SetActorTransform(InitialMainContainerTransform);

                FluidSampleActor->U_FluidMainContainer->Delta_Position = InitialDeltaPosition;
                FluidSampleActor->U_FluidMainContainer->Delta_Orientation = InitialDeltaOrientation;
            }
            if (FluidSampleActor->U_FluidDestinationContainer)
            {
                FluidSampleActor->U_FluidDestinationContainer->SetActorTransform(InitialDestinationContainerTransform);
            }
    }

    if (FluidSampleActor->U_ShouldBegin)
    {
        FluidSampleActor->U_FluidEmitter->StartEmission(InitialFluidTransform);
    }
}

void UFluidGradientDescentOptimizer::ExportHistoryToCSV()
{
    FString CSVContent = TEXT("Iteration,TotalNormalizedError,")
                         TEXT("ParamScale,ParamDensity,ParamFriction,ParamRestitution,ParamDestructibility,ParamAngularDamping,ParamLinearDamping,ParamCovalentBondLength,ParamCovalentBondForce,ParamBondThickness,")
                         TEXT("Target_FlowTime,Target_SpreadArea,Target_Spillage,Target_Overflow,Target_Volume,Target_TipOver,Target_Occupancy,")
                         TEXT("Observed_FlowTime,Observed_SpreadArea,Observed_Spillage,Observed_Overflow,Observed_Volume,Observed_TipOver,Observed_Occupancy,")
                         TEXT("Error_FlowTime,Error_SpreadArea,Error_Spillage,Error_Overflow,Error_Volume,Error_TipOver,Error_Occupancy\n");

    for (const auto& Rec : History)
    {
        CSVContent += FString::Printf(TEXT("%d,%f,")
                                      TEXT("%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,")
                                      TEXT("%f,%f,%f,%f,%f,%f,%f,")
                                      TEXT("%f,%f,%f,%f,%f,%f,%f,")
                                      TEXT("%f,%f,%f,%f,%f,%f,%f\n"),
            Rec.Iteration, Rec.TotalError,
            Rec.ParamScale, Rec.ParamDensity, Rec.ParamFriction, Rec.ParamRestitution, Rec.ParamDestructibility, Rec.ParamAngularDamping, Rec.ParamLinearDamping, Rec.ParamCovalentBondLength, Rec.ParamCovalentBondForce, Rec.ParamBondThickness,
            Rec.Target_FlowTime, Rec.Target_SpreadArea, Rec.Target_Spillage, Rec.Target_Overflow, Rec.Target_Volume, Rec.Target_TipOver, Rec.Target_Occupancy,
            Rec.Observed_FlowTime, Rec.Observed_SpreadArea, Rec.Observed_Spillage, Rec.Observed_Overflow, Rec.Observed_Volume, Rec.Observed_TipOver, Rec.Observed_Occupancy,
            Rec.Error_FlowTime, Rec.Error_SpreadArea, Rec.Error_Spillage, Rec.Error_Overflow, Rec.Error_Volume, Rec.Error_TipOver, Rec.Error_Occupancy);
    }

    FString FullPath = FPaths::ProjectSavedDir() + ExportFileName + TEXT(".csv");
    FFileHelper::SaveStringToFile(CSVContent, *FullPath);

    UE_LOG(LogTemp, Warning, TEXT("Fluid Optimizer Audit Log: Exported complete parameter, target, output, and loss matrix to: %s"), *FullPath);
}

float UFluidGradientDescentOptimizer::ComputeTipOver()
{
    return FluidSampleActor ? FluidSampleActor->CachedTipOver : 0.0f;
}

float UFluidGradientDescentOptimizer::ComputeOccupancy()
{
    return FluidSampleActor ? FluidSampleActor->CalculateProjectedOccupiedArea() : 0.0f;
}

float UFluidGradientDescentOptimizer::ComputeSpillage()
{
    return FluidSampleActor ? FluidSampleActor->bIsSpilledFlag : 0.0f;
}

float UFluidGradientDescentOptimizer::ComputeOverflow()
{
    return FluidSampleActor ? FluidSampleActor->bIsOverflowFlag : 0.0f;
}

float UFluidGradientDescentOptimizer::ComputeVolume()
{
    return FluidSampleActor ? FluidSampleActor->CachedTargetVolume : 0.0f;
}

float UFluidGradientDescentOptimizer::ComputeSpreadArea(float thresholdPercent, float thresholdDistance)
{
    return FluidSampleActor ? FluidSampleActor->EstimateSpreadArea(thresholdPercent, thresholdDistance) : 0.0f;
}

float UFluidGradientDescentOptimizer::ComputeFlowTime()
{
    if (FluidSampleActor)
    {
        FluidSampleActor->CachedFlowTime = EffectiveFlowTime;
        return FluidSampleActor->CachedFlowTime;
    }
    return EffectiveFlowTime;
}

bool UFluidGradientDescentOptimizer::Manipulation()
{
    if (!FluidSampleActor || !FluidSampleActor->U_FluidMainContainer)
    {
        return false;
    }

    AUFluidSmartSource* MainContainer = FluidSampleActor->U_FluidMainContainer;

    // Reset control flags
    MainContainer->Tilt_Right = false;
    MainContainer->Tilt_Left = false;
    MainContainer->Move_Up = false;
    MainContainer->Move_Down = false;
    MainContainer->Move_Front = false;
    MainContainer->Move_Back = false;
    MainContainer->Move_Left = false;
    MainContainer->Move_Right = false;

    // Manipulation is finished when all target deltas are negative
    if (TargetTiltDelta < 0.0f && TargetMoveVerticalDelta < 0.0f && TargetMoveHorizontalDelta < 0.0f)
    {
        return false;
    }

    float BasePosStep = (InitialDeltaPosition > 0.0f) ? InitialDeltaPosition : 1.0f;
    float BaseOriStep = (InitialDeltaOrientation > 0.0f) ? InitialDeltaOrientation : 1.0f;

    // Process one action per tick to avoid flag/property collisions
    if (TargetMoveVerticalDelta >= 0.0f)
    {
        MainContainer->Delta_Position = BasePosStep;
        if (TargetMoveVerticalDelta < BasePosStep)
        {
            MainContainer->Delta_Position = TargetMoveVerticalDelta;
            TargetMoveVerticalDelta = -1.0f;
        }
        else
        {
            TargetMoveVerticalDelta -= BasePosStep;
        }
        MainContainer->Move_Up = true;
    }
    else if (TargetMoveHorizontalDelta >= 0.0f)
    {
        MainContainer->Delta_Position = BasePosStep;
        if (TargetMoveHorizontalDelta < BasePosStep)
        {
            MainContainer->Delta_Position = TargetMoveHorizontalDelta;
            TargetMoveHorizontalDelta = -1.0f;
        }
        else
        {
            TargetMoveHorizontalDelta -= BasePosStep;
        }
        MainContainer->Move_Front = true;
    }
    else if (TargetTiltDelta >= 0.0f)
    {
        MainContainer->Delta_Orientation = BaseOriStep;
        if (TargetTiltDelta < BaseOriStep)
        {
            MainContainer->Delta_Orientation = TargetTiltDelta;
            TargetTiltDelta = -1.0f;
        }
        else
        {
            TargetTiltDelta -= BaseOriStep;
        }
        MainContainer->Tilt_Right = true;
    }

    MainContainer->Control();
    return true;
}
