// Fill out your copyright notice in the Description page of Project Settings.

#include "UFluidSample.h"
#include <omp.h>
#include "Materials/MaterialInstanceDynamic.h" // Required for runtime parameter adjustments
#include "Materials/Material.h"                 // Ensures the compiler understands UMaterial casting

// Sets default values
AUFluidSample::AUFluidSample()
{
    UE_LOG(LogTemp, Warning, TEXT("----------------------------------- CREATING SAMPLE ---------------------------------------"));

    USceneComponent* rootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("FluidSample"));
    this->SetRootComponent(rootComponent);

    U_CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    U_CameraBoom->SetupAttachment(RootComponent);
    U_CameraBoom->TargetArmLength = 1.0f;
    U_CameraBoom->bUsePawnControlRotation = true;

    this->QUANTITY_ESCAPED = 0.0f;
    this->U_FluidMainContainer = nullptr;
    this->U_FluidDestinationContainer = nullptr;
    this->U_NumberParticles = 1;
    this->U_ParticleScale = FVector(0.01f, 0.01f, 0.01f);
    this->Vertices = {};
    this->Indices = {};
    this->DrawGroupIndices = {};

    this->U_FluidState = FS_CREATED;
    this->U_FluidEmitter = nullptr;
    this->U_ShouldBegin = false;
    this->U_Color = false;
    this->U_FluidMass=0.001;
    this->U_FluidLinearDamping = 1.0;
    this->U_FluidMesh = nullptr;
    this->U_PhysicalMaterial = nullptr;
    this->U_FluidDestructibility=0.0;

    this->Sample_Color = FColor::Red;

    // Load the master material asset directly from your UFluid Plugin Content subdirectory
    static ConstructorHelpers::FObjectFinder<UMaterial> FoundMaterial(TEXT("/UFluid/Bond/M_FluidMaterial.M_FluidMaterial"));
    if (FoundMaterial.Succeeded())
    {
        this->U_Material = FoundMaterial.Object;
    }
    else
    {
        this->U_Material = nullptr;
        UE_LOG(LogTemp, Error, TEXT("AUFluidSample: Failed to find Master Material at '/UFluid/Bond/M_FluidMaterial.M_FluidMaterial'!"));
    }

    U_FollowCamera = CreateDefaultSubobject<UFluidSceneCaptureComponent2D>(TEXT("FollowCamera"));
    U_FollowCamera->TextureTarget = NewObject<UTextureRenderTarget2D>();
    U_FollowCamera->TextureTarget->InitAutoFormat(640, 480);
    U_FollowCamera->TextureTarget->UpdateResourceImmediate();
    U_FollowCamera->CaptureSource = SCS_SceneColorHDR;
    U_FollowCamera->SetupAttachment(U_CameraBoom, USpringArmComponent::SocketName);
    U_FollowCamera->bCaptureEveryFrame = true;

    this->U_CovalentBond = 10.0f;
    this->U_CovalentBondTickness = 1.0f;
    this->U_CovalentBondForce=0.0f;

    Should_Use_Fluid = false;

    LineBatcher = CreateDefaultSubobject<ULineBatchComponent>(TEXT("LineBatcher"));
    Lines = {};

    // Build the procedural mesh component pipeline
    FluidMeshComponent = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("FluidMeshComponent"));
    FluidMeshComponent->SetupAttachment(RootComponent);

    // Prevent the procedural component from initiating scene physics queries or tracking collisions
    FluidMeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    FluidMeshComponent->SetCollisionResponseToAllChannels(ECR_Ignore);

    PrimaryActorTick.bCanEverTick = true;
}

AUFluidSample::~AUFluidSample()
{
    UE_LOG(LogTemp, Warning, TEXT("----------------------------------- KILLING SAMPLE ---------------------------------------"));
}

void AUFluidSample::BeginPlay()
{
    Super::BeginPlay();
    this->U_WorldHandle = GetWorld();

    this->U_FluidEmitter = NewObject<UUFluidEmitter>();
    this->U_FluidEmitter->U_WorldHandle = this->U_WorldHandle;
    this->U_FluidEmitter->U_ParticleModel->Linear_Damping = this->U_FluidLinearDamping;
    this->U_FluidEmitter->U_ParticleModel->Angular_Damping = this->U_FluidAngularDamping;
    this->U_FluidEmitter->U_ParticleModel->Mass=this->U_FluidMass;
    this->U_FluidEmitter->U_ParticleModel->Destructibility=this->U_FluidDestructibility;
    this->U_FluidEmitter->U_ParticleModel->Restitution=this->U_FluidRestitution;
    this->U_FluidEmitter->U_ParticleModel->Friction=this->U_FluidFriction;
    this->U_FluidEmitter->U_ParticleModel->Density=this->U_FluidDensity;

    UE_LOG(LogTemp, Warning, TEXT("----------------------------------- BEGINNING SAMPLE ---------------------------------------"));
    //this->U_ShouldBegin = true;
    this->U_FluidEmitter->U_Color = this->U_Color;
    this->U_FluidEmitter->U_ParticleModel->Scale = U_ParticleScale;
    this->U_FluidEmitter->U_NumberParticles = this->U_NumberParticles;
    this->U_FluidEmitter->U_ParticleModel->U_StaticMesh = this->U_FluidMesh;
    this->U_FluidEmitter->U_ParticleModel->U_PhysicalMaterial = this->U_PhysicalMaterial;

    // Instantiates an isolated material instance dynamic specifically tracking the Procedural Mesh surface
    if (this->U_Material && FluidMeshComponent)
    {
        UMaterialInstanceDynamic* DynamicMaterial = UMaterialInstanceDynamic::Create(this->U_Material, this);
        if (DynamicMaterial)
        {
            // Update parameter value clean without corrupting original particle master material paths
            DynamicMaterial->SetVectorParameterValue(FName("Color"), FLinearColor(this->Sample_Color));
            FluidMeshComponent->SetMaterial(0, DynamicMaterial);
        }
    }

    // Keep the emitter bound cleanly to the foundational default material object pipeline
    if (this->U_FluidEmitter && this->U_FluidEmitter->U_ParticleModel)
    {
        this->U_FluidEmitter->U_ParticleModel->U_Material = this->U_Material;
    }
}

void AUFluidSample::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    if (this->U_ShouldBegin && this->U_FluidEmitter)
        this->U_FluidEmitter->StartEmission(FTransform(GetActorRotation(), GetActorLocation(), GetActorScale()));

    FL0OrientedBox sbbox = AUFluidSample::CalculateActorOrientedBoundingBox(this->U_FluidMainContainer);
    AUFluidSample::DrawDebugOrientedBox(this->U_WorldHandle, sbbox, FColor::Red, 1.0, FVector(0.0, 0.0, 0.0));

    FL0OrientedBox dbbox = AUFluidSample::CalculateActorOrientedBoundingBox(this->U_FluidDestinationContainer);
    AUFluidSample::DrawDebugOrientedBox(this->U_WorldHandle, dbbox, FColor::Blue, 1.0, FVector(0.0, 0.0, 0.0));

    // Save the initial transform of the container on the first execution frame
    if (!bIsInitialTransformSaved)
    {
        InitialContainerTransform = U_FluidMainContainer->GetActorTransform();
        bIsInitialTransformSaved = true;
        UE_LOG(LogTemp, Log, TEXT("[HumanManipulation] Initial container transform saved at Location: %s, Rotation: %s"),
            *InitialContainerTransform.GetLocation().ToString(),
            *InitialContainerTransform.GetRotation().Rotator().ToString());
    }
    AUFluidSample::BuildFluidMesh();
    Manipulate();
    if (this->U_FluidEmitter)
        Should_Use_Fluid = this->U_FluidEmitter->Fluid_Created;
}

bool AUFluidSample::DeleteSample()
{
    if (!this->U_FluidEmitter) return false;

    int32 ParticleCount = this->U_FluidEmitter->U_FluidParticles.Num();
    UE_LOG(LogTemp, Warning, TEXT("------------------ BEGIN KILLING PARTICLES: %d ------------------"), ParticleCount);

    for (int i = 0; i < ParticleCount; i++)
    {
        if (this->U_FluidEmitter->U_FluidParticles[i])
        {
            this->U_FluidEmitter->U_FluidParticles[i]->DeleteParticle();
            if (this->U_FluidEmitter->U_FluidParticles[i]->IsValidLowLevel())
            {
                this->U_FluidEmitter->U_FluidParticles[i]->ConditionalBeginDestroy();
            }
            this->U_FluidEmitter->U_FluidParticles[i] = nullptr;
        }
    }
    this->U_FluidEmitter->U_FluidParticles.Empty();

    if (this->U_FluidEmitter->IsValidLowLevel())
    {
        this->U_FluidEmitter->ConditionalBeginDestroy();
    }
    this->U_FluidEmitter = nullptr;
    return true;
}

FL0OrientedBox AUFluidSample::CalculateActorOrientedBoundingBox(AUFluidSmartSource* Container)
{
    if (!Container) return FL0OrientedBox();

    const FBox Box = Container->CalculateComponentsBoundingBoxInLocalSpace();
    const auto Transform = Container->GetTransform();

    FL0OrientedBox OrientedBox;
    OrientedBox.Center = Transform.TransformPosition(Box.GetCenter());

    const FVector Extent = Box.GetExtent() + Container->BoundaryOffset;
    OrientedBox.Forward = Transform.TransformVector(FVector::ForwardVector * Extent.X);
    OrientedBox.Right = Transform.TransformVector(FVector::RightVector * Extent.Y);
    OrientedBox.Up = Transform.TransformVector(FVector::UpVector * Extent.Z);

    return OrientedBox;
}

// 32-core OpenMP High-Performance 3D Ribbon Mesh Generation Pipeline with Pairwise Axial Physics
bool AUFluidSample::BuildFluidMesh()
{
    if (!FluidMeshComponent) return false;

    if (!this->U_FluidEmitter || this->U_FluidEmitter->U_FluidParticles.Num() < 2)
    {
        FluidMeshComponent->ClearAllMeshSections();
        return false;
    }

    float threshold = this->U_CovalentBond;
    float Thickness = this->U_CovalentBondTickness;

    // Clear tracking arrays
    this->Vertices.Reset();
    this->Indices.Reset();

    int32 TotalParticles = this->U_FluidEmitter->U_FluidParticles.Num();
    UUFluidParticle** ParticleDataPtr = this->U_FluidEmitter->U_FluidParticles.GetData();

    // 1. Project world locations into local actor space and cache world positions
    TArray<FVector> Locations;
    Locations.SetNumUninitialized(TotalParticles);
    FVector* LocationsPtr = Locations.GetData();

    TArray<FVector> WorldLocations;
    WorldLocations.SetNumUninitialized(TotalParticles);
    FVector* WorldLocationsPtr = WorldLocations.GetData();

    for (int32 i = 0; i < TotalParticles; i++)
    {
        if (ParticleDataPtr[i] && ParticleDataPtr[i]->U_StaticMeshActor)
        {
            WorldLocationsPtr[i] = ParticleDataPtr[i]->U_StaticMeshActor->GetActorLocation();
            LocationsPtr[i] = this->GetTransform().InverseTransformPosition(WorldLocationsPtr[i]);
        }
        else
        {
            WorldLocationsPtr[i] = FVector::ZeroVector;
            LocationsPtr[i] = FVector::ZeroVector;
        }
    }

    // 2. Setup thread-local buffers to completely bypass locking overhead
    struct FLinePair { FVector Start; FVector End; };
    TArray<TArray<FLinePair>> ThreadLocalLineBuffers;
    TArray<TArray<FVector>> ThreadLocalForceBuffers;

    int32 MaxThreads = omp_get_max_threads();
    ThreadLocalLineBuffers.SetNum(MaxThreads);
    ThreadLocalForceBuffers.SetNum(MaxThreads);

    for (int32 t = 0; t < MaxThreads; t++)
    {
        ThreadLocalForceBuffers[t].Init(FVector::ZeroVector, TotalParticles);
    }

    float BondForceMagnitude = this->U_CovalentBondForce;

    // 3. Dual-loop spatial proximity & thread-safe force accumulation using OpenMP
    #pragma omp parallel
    {
        int32 ThreadID = omp_get_thread_num();
        TArray<FLinePair>& LocalBuffer = ThreadLocalLineBuffers[ThreadID];
        TArray<FVector>& LocalForceBuffer = ThreadLocalForceBuffers[ThreadID];

        #pragma omp for schedule(dynamic, 16)
        for (int32 i = 0; i < TotalParticles - 1; i++)
        {
            FVector PosI = LocationsPtr[i];
            if (PosI.IsZero()) continue;

            for (int32 j = i + 1; j < TotalParticles; j++)
            {
                FVector PosJ = LocationsPtr[j];
                if (PosJ.IsZero()) continue;

                float DistSq = FVector::DistSquared(PosI, PosJ);
                if (DistSq <= FMath::Square(threshold))
                {
                    // Only generate visual ribbon geometry if Thickness > 0.0f
                    if (Thickness > 0.0f)
                    {
                        LocalBuffer.Add({PosI, PosJ});
                    }

                    // Compute axial force if force magnitude is non-zero
                    if (FMath::Abs(BondForceMagnitude) > 0.0f)
                    {
                        float Dist = FMath::Sqrt(DistSq);
                        if (Dist > 0.0001f)
                        {
                            // Axis unit vector pointing from particle i to particle j in World Space
                            FVector WorldDir = (WorldLocationsPtr[j] - WorldLocationsPtr[i]) / Dist;

                            // Positive = Attraction (pulls i to j), Negative = Repulsion (pushes i away from j)
                            FVector PairForce = WorldDir * BondForceMagnitude;

                            LocalForceBuffer[i] += PairForce;
                            LocalForceBuffer[j] -= PairForce;
                        }
                    }
                }
            }
        }
    }

    // Apply accumulated pairwise physics forces to particles safely
    if (FMath::Abs(BondForceMagnitude) > 0.0f)
    {
        for (int32 i = 0; i < TotalParticles; i++)
        {
            FVector TotalParticleForce = FVector::ZeroVector;
            for (int32 t = 0; t < MaxThreads; t++)
            {
                TotalParticleForce += ThreadLocalForceBuffers[t][i];
            }

            if (!TotalParticleForce.IsNearlyZero() && ParticleDataPtr[i] && ParticleDataPtr[i]->U_StaticMeshActor)
            {
                UPrimitiveComponent* PrimComp = Cast<UPrimitiveComponent>(ParticleDataPtr[i]->U_StaticMeshActor->GetRootComponent());
                if (PrimComp && PrimComp->IsSimulatingPhysics())
                {
                    PrimComp->AddForce(TotalParticleForce, NAME_None, true);
                }
            }
        }
    }

    // Secondary structural rendering buffers
    TArray<FLinearColor> VertexColors;
    TArray<FVector> Normals;
    TArray<FVector2D> UV0;
    TArray<FProcMeshTangent> Tangents;

    FLinearColor FluidLinearColor = FLinearColor(this->Sample_Color);
    FVector UpVector = FVector::UpVector;

    // 4. Merge threads sequentially while generating mathematically correct 3D surfaces
    for (int32 t = 0; t < MaxThreads; t++)
    {
        for (const FLinePair& Pair : ThreadLocalLineBuffers[t])
        {
            FVector Direction = (Pair.End - Pair.Start).GetSafeNormal();
            if (Direction.IsNearlyZero()) continue;

            // Generate a perpendicular cross-vector to map width/thickness offsets
            FVector RightVector = FVector::CrossProduct(Direction, UpVector).GetSafeNormal() * (Thickness * 0.5f);
            if (RightVector.IsNearlyZero())
            {
                RightVector = FVector::RightVector * (Thickness * 0.5f);
            }

            int32 VIndex = this->Vertices.Num();

            FVector V0 = Pair.Start - RightVector;
            FVector V1 = Pair.Start + RightVector;
            FVector V2 = Pair.End - RightVector;
            FVector V3 = Pair.End + RightVector;

            this->Vertices.Add(V0);
            this->Vertices.Add(V1);
            this->Vertices.Add(V2);
            this->Vertices.Add(V3);

            // FIXED NORMALS: Inverted the cross product vector to match the new upward-facing winding order seamlessly
            FVector Normal = FVector::CrossProduct(RightVector, Direction).GetSafeNormal();
            if (Normal.IsNearlyZero()) Normal = FVector::UpVector;

            Normals.Add(Normal); Normals.Add(Normal); Normals.Add(Normal); Normals.Add(Normal);

            // Supply vertex colors
            VertexColors.Add(FluidLinearColor);
            VertexColors.Add(FluidLinearColor);
            VertexColors.Add(FluidLinearColor);
            VertexColors.Add(FluidLinearColor);

            // Establish standard coordinate mappings
            UV0.Add(FVector2D(0.0f, 0.0f));
            UV0.Add(FVector2D(1.0f, 0.0f));
            UV0.Add(FVector2D(0.0f, 1.0f));
            UV0.Add(FVector2D(1.0f, 1.0f));

            // FIXED WINDING ORDER: Map 2 triangles facing upwards to receive lights correctly from above
            this->Indices.Add(VIndex + 0);
            this->Indices.Add(VIndex + 3);
            this->Indices.Add(VIndex + 1);

            this->Indices.Add(VIndex + 0);
            this->Indices.Add(VIndex + 2);
            this->Indices.Add(VIndex + 3);
        }
    }

    // 5. Safely ship completely finalized buffers to your hardware graphics hardware
    if (this->Vertices.Num() > 0)
    {
        // Extract dynamically assigned material index cleanly from mesh mapping layer
        UMaterialInstanceDynamic* DynamicMat = Cast<UMaterialInstanceDynamic>(FluidMeshComponent->GetMaterial(0));
        if (DynamicMat)
        {
            DynamicMat->SetVectorParameterValue(FName("Color"), FluidLinearColor);
        }

        // FIXED COLLISIONS: Last parameter is strictly set to false to completely turn off physical procedural mesh collision data
        FluidMeshComponent->CreateMeshSection_LinearColor(0, this->Vertices, this->Indices, Normals, UV0, VertexColors, Tangents, false);
        return true;
    }
    else
    {
        FluidMeshComponent->ClearAllMeshSections();
    }

    return false;
}

bool AUFluidSample::DrawDebugOrientedBox(UWorld* World, const FL0OrientedBox& Box, const FColor& Color, float LifeTime, FVector TargetParticle)
{
    const FVector Center = Box.Center;
    const FVector Right = Box.Right;
    const FVector Up = Box.Up;
    const FVector Forward = Box.Forward;

    const FVector Delta = Center - TargetParticle;

    return (FMath::Abs(Delta.X) <= FMath::Sqrt(Right.SizeSquared())) &&
           (FMath::Abs(Delta.Y) <= FMath::Sqrt(Up.SizeSquared())) &&
           (FMath::Abs(Delta.Z) <= FMath::Sqrt(Forward.SizeSquared()));
}

FText AUFluidSample::UpdateFluidIDHUD()
{
    return FText::FromString(FString("Id 0"));
}

float AUFluidSample::UpdateSampleHUD()
{
    float AmountFluidTXT = 0.0f;
    AUFluidSmartSource* target_container = (this->U_FluidState == FS_FILLING) ? this->U_FluidMainContainer : this->U_FluidDestinationContainer;

    if (!target_container && this->U_FluidState != FS_FILLING && this->U_FluidState != FS_POURING)
    {
        target_container = this->U_FluidDestinationContainer;
        if (this->U_FluidEmitter)
        {
            int32 ParticleCount = this->U_FluidEmitter->U_FluidParticles.Num();
            UUFluidParticle** ParticleDataPtr = this->U_FluidEmitter->U_FluidParticles.GetData();

            #pragma omp parallel for schedule(static)
            for (int32 i = 0; i < ParticleCount; i++)
            {
                if (ParticleDataPtr[i]) ParticleDataPtr[i]->U_State = S_TRANSITING;
            }
        }
    }

    if (this->U_FluidEmitter && target_container)
    {
        int32 ParticleCount = this->U_FluidEmitter->U_FluidParticles.Num();
        float TotalPotential = ParticleCount + this->U_FluidEmitter->U_NumberParticles;

        if (TotalPotential > 0.0f)
        {
            FL0OrientedBox obbox = AUFluidSample::CalculateActorOrientedBoundingBox(target_container);
            UUFluidParticle** ParticleDataPtr = this->U_FluidEmitter->U_FluidParticles.GetData();
            int32 ContainedCount = 0;

            #pragma omp parallel for reduction(+:ContainedCount) schedule(static)
            for (int32 i = 0; i < ParticleCount; i++)
            {
                if (ParticleDataPtr[i] && ParticleDataPtr[i]->U_StaticMeshActor)
                {
                    FVector PLoc = ParticleDataPtr[i]->U_StaticMeshActor->GetActorLocation();
                    if (AUFluidSample::IsPointInsideOOB( obbox,PLoc))
                    {
                        ContainedCount++;
                        ParticleDataPtr[i]->U_State = S_CONTAINED;
                    }
                }
            }
            AmountFluidTXT = (100.0f * (float)ContainedCount) / TotalPotential;
        }
    }
    return AmountFluidTXT;
}


bool AUFluidSample::IsPointInsideOOB(const FL0OrientedBox& Box, const FVector& Point)
{
    // Get the relative vector from the center of the box to the point
    const FVector Delta = Point - Box.Center;

    // Check Forward axis (X)
    const float ForwardDot = FVector::DotProduct(Delta, Box.Forward);
    if (FMath::Abs(ForwardDot) > Box.Forward.SizeSquared())
    {
        return false;
    }

    // Check Right axis (Y)
    const float RightDot = FVector::DotProduct(Delta, Box.Right);
    if (FMath::Abs(RightDot) > Box.Right.SizeSquared())
    {
        return false;
    }

    // Check Up axis (Z) - This fixes the bottom half issue!
    const float UpDot = FVector::DotProduct(Delta, Box.Up);
    if (FMath::Abs(UpDot) > Box.Up.SizeSquared())
    {
        return false;
    }

    // Point passed all three axis checks, meaning it is inside the box
    return true;
}


float AUFluidSample::UpdateEscapedHUD()
{
    float escaped = 0.0f;
    AUFluidSmartSource* target_container = (this->U_FluidState == FS_FILLING) ? this->U_FluidMainContainer : this->U_FluidDestinationContainer;

    if (this->U_FluidEmitter)
    {
        int32 ParticleCount = this->U_FluidEmitter->U_FluidParticles.Num();
        float TotalPotential = ParticleCount + this->U_FluidEmitter->U_NumberParticles;

        if (TotalPotential > 0.0f)
        {
            int32 OutCount = 0;
            if (target_container)
            {
                FL0OrientedBox obbox = AUFluidSample::CalculateActorOrientedBoundingBox(target_container);
                UUFluidParticle** ParticleDataPtr = this->U_FluidEmitter->U_FluidParticles.GetData();

                #pragma omp parallel for reduction(+:OutCount) schedule(static)
                for (int32 i = 0; i < ParticleCount; i++)
                {
                    if (ParticleDataPtr[i] && ParticleDataPtr[i]->U_StaticMeshActor)
                    {
                        FVector PLoc = ParticleDataPtr[i]->U_StaticMeshActor->GetActorLocation();
                        if (!AUFluidSample::IsPointInsideOOB( obbox,PLoc))
                        {
                            OutCount++;
                        }
                    }
                    else
                    {
                        OutCount++;
                    }
                }
            }
            else
            {
                OutCount = ParticleCount;
            }

            escaped = this->U_FluidEmitter->U_NumberParticles + OutCount;
            escaped = (100.0f * escaped) / TotalPotential;
        }
    }
    this->QUANTITY_ESCAPED = escaped;
    this->CachedTargetVolume=1.0f-escaped/100.0f;
    return escaped;
}

bool AUFluidSample::UpdateMissDetectedHUD()
{
    float miss_probability = 0.0f;
    float ThresholdPercentage = 5.0f; // Variable threshold percentage (e.g., 5%)

    if (this->U_FluidEmitter)
    {
        int32 ParticleCount = this->U_FluidEmitter->U_FluidParticles.Num();
        float TotalPotential = ParticleCount + this->U_FluidEmitter->U_NumberParticles;

        if (TotalPotential > 0.0f)
        {
            AUFluidSmartSource* target_container = (this->U_FluidState == FS_FILLING) ? this->U_FluidMainContainer : this->U_FluidDestinationContainer;
            int32 MissCount = 0;

            if (target_container)
            {
                FL0OrientedBox obbox = AUFluidSample::CalculateActorOrientedBoundingBox(target_container);
                float ContainerZ = target_container->GetActorLocation().Z;
                UUFluidParticle** ParticleDataPtr = this->U_FluidEmitter->U_FluidParticles.GetData();

                #pragma omp parallel for reduction(+:MissCount) schedule(static)
                for (int32 i = 0; i < ParticleCount; i++)
                {
                    if (ParticleDataPtr[i] && ParticleDataPtr[i]->U_StaticMeshActor)
                    {
                        FVector PLoc = ParticleDataPtr[i]->U_StaticMeshActor->GetActorLocation();
                        if (!AUFluidSample::IsPointInsideOOB(obbox, PLoc))
                        {
                            if (PLoc.Z <= ContainerZ && ParticleDataPtr[i]->U_State != S_CONTAINED)
                            {
                                MissCount++;
                            }
                        }
                    }
                    else
                    {
                        MissCount++;
                    }
                }
            }
            else
            {
                MissCount = ParticleCount;
            }

            miss_probability = (100.0f * (float)MissCount) / TotalPotential;
        }
    }

    if (miss_probability >= ThresholdPercentage)
    {
        this->bIsSpilledFlag = 1.0f;
    }
    else
    {
        this->bIsSpilledFlag = FMath::Clamp(miss_probability / ThresholdPercentage, 0.0f, 1.0f);
    }

    return (miss_probability >= ThresholdPercentage);
}

bool AUFluidSample::UpdateSpillageDetectedHUD()
{
    float spillage_probability = 1.0f;
    float threshold = 0.6f;

    if (this->U_FluidEmitter)
    {
        if (this->U_FluidEmitter->U_FluidParticles.Num() + this->U_FluidEmitter->U_NumberParticles >= 0.0f)
        {
            if (this->U_FluidState == FS_POURING && this->U_FluidDestinationContainer)
            {
                FVector ContainerNormal = this->U_FluidDestinationContainer->ContainerNormal;
                FVector ContainerPoseAxis = this->U_FluidDestinationContainer->GetActorRotation().Quaternion().GetUpVector();

                float dotproduct = FVector::DotProduct(ContainerNormal, ContainerPoseAxis);
                float norm1 = ContainerPoseAxis.Size();
                float norm2 = ContainerNormal.Size();

                if (norm1 * norm2 > 0.0f)
                {
                    spillage_probability = dotproduct / (norm1 * norm2);
                }
            }
        }
    }

    if (spillage_probability <= threshold)
    {
        this->CachedTipOver = 1.0f;
    }
    else
    {
        this->CachedTipOver = FMath::Clamp(1.0f - ((spillage_probability - threshold) / (1.0f - threshold)), 0.0f, 1.0f);
    }

    return (spillage_probability <= threshold);
}

float AUFluidSample::EstimateSpreadArea(float ThresholdPercent, float ThresholdDistance)
{
    UUFluidEmitter* Emitter = this->U_FluidEmitter;
    if (!Emitter || Emitter->U_FluidParticles.Num() == 0) return 0.0f;

    int32 ParticleCount = Emitter->U_FluidParticles.Num();
    UUFluidParticle** AllParticles = Emitter->U_FluidParticles.GetData();

    TArray<FVector> Locations;
    Locations.SetNumUninitialized(ParticleCount);
    FVector* LocsPtr = Locations.GetData();

    for (int32 i = 0; i < ParticleCount; i++)
    {
        LocsPtr[i] = AllParticles[i] ? AllParticles[i]->U_StaticMeshActor->GetActorLocation() : FVector::ZeroVector;
    }

    TArray<FVector> FilteredPoints;
    FilteredPoints.Reserve(ParticleCount);
    float DistanceSqLimit = FMath::Square(ThresholdDistance);

    int32 MaxThreads = omp_get_max_threads();
    TArray<TArray<FVector>> ThreadBuffers;
    ThreadBuffers.SetNum(MaxThreads);

    #pragma omp parallel
    {
        int32 ThreadID = omp_get_thread_num();
        TArray<FVector>& LocalBuf = ThreadBuffers[ThreadID];

        #pragma omp for schedule(static)
        for (int32 i = 0; i < ParticleCount; ++i)
        {
            FVector PosI = LocsPtr[i];
            if (PosI.IsZero()) continue;
            bool bIsIsolated = true;

            for (int32 j = 0; j < ParticleCount; ++j)
            {
                if (i == j || LocsPtr[j].IsZero()) continue;
                if (FVector::DistSquaredXY(PosI, LocsPtr[j]) <= DistanceSqLimit)
                {
                    bIsIsolated = false;
                    break;
                }
            }
            if (!bIsIsolated) LocalBuf.Add(FVector(PosI.X, PosI.Y, 0.0f));
        }
    }

    for (int32 t = 0; t < MaxThreads; t++)
    {
        FilteredPoints.Append(ThreadBuffers[t]);
    }

    int32 FilteredCount = FilteredPoints.Num();
    if (FilteredCount == 0) return 0.0f;

    double CentroidX = 0.0, CentroidY = 0.0;
    const FVector* FilteredPtr = FilteredPoints.GetData();

    #pragma omp parallel for reduction(+:CentroidX, CentroidY) schedule(static)
    for (int32 i = 0; i < FilteredCount; i++)
    {
        CentroidX += FilteredPtr[i].X;
        CentroidY += FilteredPtr[i].Y;
    }
    FVector Centroid = FVector(CentroidX / FilteredCount, CentroidY / FilteredCount, 0.0f);

    TArray<float> DistancesSq;
    DistancesSq.SetNumUninitialized(FilteredCount);
    float* DistSqPtr = DistancesSq.GetData();

    #pragma omp parallel for schedule(static)
    for (int32 i = 0; i < FilteredCount; i++)
    {
        DistSqPtr[i] = FVector::DistSquaredXY(FilteredPtr[i], Centroid);
    }
    DistancesSq.Sort();

    int32 Index = FMath::Clamp(FMath::FloorToInt(FilteredCount * (ThresholdPercent / 100.0f)), 0, FilteredCount - 1);
    float RadiusSq = DistancesSq[Index];
    float Radius = FMath::Sqrt(RadiusSq);

    DrawDebugCircle(GetWorld(), Centroid + FVector(0, 0, 5), Radius, 32, FColor::Green, false, 10.1f, 0, 2.0f, FVector(1, 0, 0), FVector(0, 1, 0));

    this->CachedSpreadArea=PI * RadiusSq;
    UE_LOG(LogTemp, Warning, TEXT("++++++++++++++++++++++++++++++  Radius Area: %f %f **********************************************************"), Radius, this->CachedSpreadArea);
    return this->CachedSpreadArea;
}

bool AUFluidSample::UpdateOverflowDetectedHUD()
{
    float overflow_probability = 0.0f;
    float ThresholdPercentage = 5.0f; // Variable threshold percentage

    if (this->U_FluidEmitter)
    {
        int32 ParticleCount = this->U_FluidEmitter->U_FluidParticles.Num();
        float TotalPotential = ParticleCount + this->U_FluidEmitter->U_NumberParticles;

        if (TotalPotential > 0.0f)
        {
            AUFluidSmartSource* target_container = (this->U_FluidState == FS_FILLING) ? this->U_FluidMainContainer : this->U_FluidDestinationContainer;
            int32 OverflowCount = 0;

            if (target_container)
            {
                FL0OrientedBox obbox = AUFluidSample::CalculateActorOrientedBoundingBox(target_container);
                float ContainerZ = target_container->GetActorLocation().Z;
                UUFluidParticle** ParticleDataPtr = this->U_FluidEmitter->U_FluidParticles.GetData();

                #pragma omp parallel for reduction(+:OverflowCount) schedule(static)
                for (int32 i = 0; i < ParticleCount; i++)
                {
                    if (ParticleDataPtr[i] && ParticleDataPtr[i]->U_StaticMeshActor)
                    {
                        FVector PLoc = ParticleDataPtr[i]->U_StaticMeshActor->GetActorLocation();
                        if (!AUFluidSample::IsPointInsideOOB(obbox, PLoc))
                        {
                            if (PLoc.Z <= ContainerZ && ParticleDataPtr[i]->U_State == S_CONTAINED)
                            {
                                OverflowCount++;
                            }
                        }
                    }
                }
            }
            overflow_probability = (100.0f * (float)OverflowCount) / TotalPotential;
        }
    }

    if (overflow_probability >= ThresholdPercentage)
    {
        this->bIsOverflowFlag = 1.0f;
    }
    else
    {
        this->bIsOverflowFlag = FMath::Clamp(overflow_probability / ThresholdPercentage, 0.0f, 1.0f);
    }

    return (overflow_probability >= ThresholdPercentage);
}



float AUFluidSample::CalculateProjectedOccupiedArea()
{
    AUFluidSmartSource* target_container = (this->U_FluidState == FS_FILLING) ? this->U_FluidMainContainer : this->U_FluidDestinationContainer;
    if (!this->U_FluidEmitter || !target_container) return 0.0f;

    int32 ParticleCount = this->U_FluidEmitter->U_FluidParticles.Num();
    if (ParticleCount <= 0) return 0.0f;

    UUFluidParticle** ParticleDataPtr = this->U_FluidEmitter->U_FluidParticles.GetData();

    // 1. Temporarily disable physics simulation to lock positions for a clean atomic snapshot
    TArray<UPrimitiveComponent*> PrimComponents;
    PrimComponents.SetNumZeroed(ParticleCount);

    for (int32 i = 0; i < ParticleCount; i++)
    {
        if (ParticleDataPtr[i] && ParticleDataPtr[i]->U_StaticMeshActor)
        {
            UPrimitiveComponent* PrimComp = Cast<UPrimitiveComponent>(ParticleDataPtr[i]->U_StaticMeshActor->GetRootComponent());
            if (PrimComp)
            {
                PrimComponents[i] = PrimComp;
                PrimComp->SetSimulatePhysics(false);
            }
        }
    }

    // 2. Establish the projection plane basis from ContainerNormal
    FVector WorldNormal = target_container->GetActorRotation().RotateVector(target_container->ContainerNormal).GetSafeNormal();
    if (WorldNormal.IsZero()) WorldNormal = FVector(0.0f, 0.0f, 1.0f);

    FVector TempUp = (FMath::Abs(WorldNormal.Z) < 0.99f) ? FVector(0, 0, 1) : FVector(0, 1, 0);
    FVector T = FVector::CrossProduct(TempUp, WorldNormal).GetSafeNormal();
    FVector B = FVector::CrossProduct(WorldNormal, T).GetSafeNormal();
    FVector ContainerOrigin = target_container->GetActorLocation();

    // Initialize GridResolution / Diameter from the cached particle side
    float GridResolution = 0.6f;
    for (int32 i = 0; i < ParticleCount; i++)
    {
        if (ParticleDataPtr[i])
        {
            GridResolution = FMath::Max(ParticleDataPtr[i]->CachedParticleSide, 0.1f);
            break;
        }
    }

    struct FProjectedParticle
    {
        FVector WorldLocation;
        float U;
        float V;
        bool bIsValid;
    };

    TArray<FProjectedParticle> Projections;
    Projections.SetNumUninitialized(ParticleCount);
    FProjectedParticle* ProjPtr = Projections.GetData();

    // 3. Extract frozen locations, world coordinates, and perform 2D projection
    int32 ValidParticleCount = 0;
    for (int32 i = 0; i < ParticleCount; i++)
    {
        if (ParticleDataPtr[i] && ParticleDataPtr[i]->U_StaticMeshActor)
        {
            FVector WorldLoc = ParticleDataPtr[i]->U_StaticMeshActor->GetActorLocation();
            FVector Delta = WorldLoc - ContainerOrigin;

            ProjPtr[i].WorldLocation = WorldLoc;
            ProjPtr[i].U = FVector::DotProduct(Delta, T);
            ProjPtr[i].V = FVector::DotProduct(Delta, B);
            ProjPtr[i].bIsValid = true;
            ValidParticleCount++;
        }
        else
        {
            ProjPtr[i].bIsValid = false;
        }
    }

    // 4. Re-enable physics simulation immediately after reading positions
    for (int32 i = 0; i < ParticleCount; i++)
    {
        if (PrimComponents[i])
        {
            PrimComponents[i]->SetSimulatePhysics(true);
        }
    }

    if (ValidParticleCount <= 0) return 0.0f;

    // 5. Use a TSet to seamlessly collect and unify active cells from both particles and mesh triangles
    TSet<FIntPoint> ActiveCells;

    for (int32 i = 0; i < ParticleCount; i++)
    {
        if (!ProjPtr[i].bIsValid) continue;

        int32 CellX = FMath::FloorToInt(ProjPtr[i].U / GridResolution);
        int32 CellY = FMath::FloorToInt(ProjPtr[i].V / GridResolution);
        ActiveCells.Add(FIntPoint(CellX, CellY));
    }

    // 6. Integrate mesh/bond surfaces using the correct class member variables (Indices and Vertices)
    if (Indices.Num() > 0 && Vertices.Num() > 0)
    {
        for (int32 i = 0; i < Indices.Num(); i += 3)
        {
            if (i + 2 >= Indices.Num()) break;

            FVector V0 = GetTransform().TransformPosition(Vertices[Indices[i]]);
            FVector V1 = GetTransform().TransformPosition(Vertices[Indices[i+1]]);
            FVector V2 = GetTransform().TransformPosition(Vertices[Indices[i+2]]);

            int32 Steps = 4;
            for (int32 x = 0; x <= Steps; ++x)
            {
                for (int32 y = 0; y <= Steps - x; ++y)
                {
                    float a = static_cast<float>(x) / Steps;
                    float b = static_cast<float>(y) / Steps;
                    float c = 1.0f - a - b;

                    FVector SamplePos = (a * V0) + (b * V1) + (c * V2);
                    FVector Delta = SamplePos - ContainerOrigin;
                    float U = FVector::DotProduct(Delta, T);
                    float V = FVector::DotProduct(Delta, B);

                    ActiveCells.Add(FIntPoint(
                        FMath::FloorToInt(U / GridResolution),
                        FMath::FloorToInt(V / GridResolution)
                    ));
                }
            }
        }
    }

    int32 ActiveCellCount = ActiveCells.Num();

    // 7. Final area calculation and logging including WorldNormal
    float CellAreaCM2 = GridResolution * GridResolution;
    this->CachedOccupancy = (float)ActiveCellCount * CellAreaCM2;

    UE_LOG(LogTemp, Log, TEXT("[Occupancy Debug] WorldNormal: (X: %.2f, Y: %.2f, Z: %.2f) | ParticleCount: %d | ValidParticles: %d | ActiveCellCount: %d | CachedOccupancy: %.2f"),
        WorldNormal.X, WorldNormal.Y, WorldNormal.Z, ParticleCount, ValidParticleCount, ActiveCellCount, this->CachedOccupancy);

    return this->CachedOccupancy;
}

// In your class source file (.cpp)

#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

void AUFluidSample::saveSignal()
{

    EstimateSpreadArea(90.0f, 50.0f);
    CalculateProjectedOccupiedArea();
    // Notification log before writing to the file
    UE_LOG(LogTemp, Log, TEXT("[Telemetry] Notice: Preparing to save current fluid signals to signal.csv..."));

    // Define the file path (saved in the project's Saved directory)
    FString FilePath = FPaths::ProjectSavedDir() / TEXT("signal.csv");

    // Check if the file already exists to determine whether to write the CSV header
    bool bFileExists = FPaths::FileExists(FilePath);

    // Format the current telemetry values into a CSV row
    FString CSVLine = FString::Printf(TEXT("%f,%f,%f,%f,%f,%f,%f\n"),
        bIsSpilledFlag,
        bIsOverflowFlag,
        CachedTipOver,
        CachedOccupancy,
        CachedFlowTime,
        CachedSpreadArea,
        CachedTargetVolume
    );

    FString FileContent = "";
    if (!bFileExists)
    {
        FString Header = TEXT("bIsSpilledFlag,bIsOverflowFlag,CachedTipOver,CachedOccupancy,CachedFlowTime,CachedSpreadArea,CachedTargetVolume\n");
        FileContent += Header;
    }
    FileContent += CSVLine;

    // Append the data to the file
    if (FFileHelper::SaveStringToFile(FileContent, *FilePath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM, &IFileManager::Get(), EFileWrite::FILEWRITE_Append))
    {
        FString AbsPath = FPaths::ConvertRelativePathToFull(FilePath);
        UE_LOG(LogTemp, Log, TEXT("[Telemetry] Successfully saved signals to: %s"), *AbsPath);
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("[Telemetry] Failed to save signal.csv!"));
    }
}

void AUFluidSample::LoadMotionTrajectory()
{
    if (bIsTrajectoryLoaded)
    {
        return;
    }

    FString FilePath = FPaths::ProjectSavedDir() / TEXT("MotionData.csv");
    TArray<FString> LineArray;

    if (!FFileHelper::LoadFileToStringArray(LineArray, *FilePath))
    {
        UE_LOG(LogTemp, Error, TEXT("[HumanManipulation] Failed to load MotionData.csv from: %s"), *FilePath);
        return;
    }

    HumanMotionTrajectory.Empty();

    // Skip header row (format: iteration,cumulative_X_cm,cumulative_Y_cm,cumulative_Z_cm,cumulative_theta_deg)
    for (int32 i = 1; i < LineArray.Num(); ++i)
    {
        FString Line = LineArray[i];
        TArray<FString> ParsedTokens;
        Line.ParseIntoArray(ParsedTokens, TEXT(","), false);

        if (ParsedTokens.Num() >= 5)
        {
            FHumanMotionStep Step;
            Step.Iteration = FCString::Atoi(*ParsedTokens[0]);
            Step.CumulativeX = FCString::Atof(*ParsedTokens[1]);
            Step.CumulativeY = FCString::Atof(*ParsedTokens[2]);
            Step.CumulativeZ = FCString::Atof(*ParsedTokens[3]);
            Step.CumulativeTheta = FCString::Atof(*ParsedTokens[4]);

            HumanMotionTrajectory.Add(Step);
        }
    }

    bIsTrajectoryLoaded = true;
    Current_Index = 0;
    UE_LOG(LogTemp, Log, TEXT("[HumanManipulation] Successfully loaded %d cumulative motion steps from MotionData.csv"), HumanMotionTrajectory.Num());
}

void AUFluidSample::Manipulate()
{
    if (!bIsTrajectoryLoaded)
    {
        LoadMotionTrajectory();
    }

    if (HumanMotionTrajectory.Num() == 0)
    {
        UE_LOG(LogTemp, Warning, TEXT("[HumanManipulation] HumanMotionTrajectory is empty. Cannot execute manipulation."));
        return;
    }

    if (Current_Index >= HumanMotionTrajectory.Num())
    {
        UE_LOG(LogTemp, Log, TEXT("[HumanManipulation] Trajectory execution completed. Current_Index has reached the end of the trajectory."));
        return;
    }

    if (!U_FluidMainContainer)
    {
        UE_LOG(LogTemp, Warning, TEXT("[HumanManipulation] U_FluidMainContainer is null. Cannot execute manipulation."));
        return;
    }

    AUFluidSmartSource* MainContainer = U_FluidMainContainer;

    // Save the initial transform of the container on the first execution frame
    if (!bIsInitialTransformSaved)
    {
        InitialContainerTransform = MainContainer->GetActorTransform();
        bIsInitialTransformSaved = true;
        UE_LOG(LogTemp, Log, TEXT("[HumanManipulation] Initial container transform saved at Location: %s, Rotation: %s"),
            *InitialContainerTransform.GetLocation().ToString(),
            *InitialContainerTransform.GetRotation().Rotator().ToString());
    }

    // Get current cumulative step data
    const FHumanMotionStep& Step = HumanMotionTrajectory[Current_Index];

    // Compute absolute target location by adding cumulative offsets (in cm) to the initial position
    FVector InitialLocation = InitialContainerTransform.GetLocation();
    FVector TargetLocation = InitialLocation + FVector(Step.CumulativeX, Step.CumulativeY, Step.CumulativeZ);

    // Compute absolute target rotation by adding cumulative theta to the initial rotation (adjust axis if needed)
    FRotator InitialRotation = InitialContainerTransform.GetRotation().Rotator();
    FRotator TargetRotation = InitialRotation;
    TargetRotation.Roll += Step.CumulativeTheta;

    // Directly teleport the actor to the target location and rotation
    bool bSuccess = MainContainer->SetActorLocationAndRotation(
        TargetLocation,
        TargetRotation,
        false,
        nullptr,
        ETeleportType::TeleportPhysics
    );

    if (bSuccess)
    {
        UE_LOG(LogTemp, Verbose, TEXT("[HumanManipulation] Teleported container to Iteration %d -> Loc: %s, Rot: %s"),
            Step.Iteration, *TargetLocation.ToString(), *TargetRotation.ToString());
    }

    // Advance to the next iteration directly
    Current_Index++;
}
