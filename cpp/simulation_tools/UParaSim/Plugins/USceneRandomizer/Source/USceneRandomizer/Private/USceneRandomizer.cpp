// Copyright Kenghagho Kenfack, 2025. All Rights Reserved.

#include "USceneRandomizer.h"
#include "Components/StaticMeshComponent.h"
#include "PhysicsEngine/PhysicsConstraintComponent.h"
#include "Kismet/KismetMathLibrary.h"
#include "UObject/ConstructorHelpers.h"

// Helper function to generate a Gaussian-distributed random number using the Box-Muller transform.
// This is used to replace the non-existent FMath::RandNorm().
float GetGaussianRandom(float InMean, float InStdDev)
{
        static bool bHasSpare = false;
        static float Rand1, Rand2;

        if (bHasSpare)
        {
                bHasSpare = false;
                return InStdDev * Rand2 + InMean;
        }

        float U, V, S;
        do
        {
                U = FMath::FRand() * 2.0f - 1.0f;
                V = FMath::FRand() * 2.0f - 1.0f;
                S = U * U + V * V;
        } while (S >= 1.0f || S == 0.0f);

        float Multiplier = FMath::Sqrt(-2.0f * FMath::Loge(S) / S);
        Rand1 = U * Multiplier;
        Rand2 = V * Multiplier;

        bHasSpare = true;

        return InStdDev * Rand1 + InMean;
}

// Sets default values
ASceneRandomizer::ASceneRandomizer()
{
        // Set this actor to call Tick() every frame. You can turn this off to improve performance if you don't need it.
        PrimaryActorTick.bCanEverTick = true;

        RANDOMIZER_TIMER=0;
        RANDOMIZER_PERIOD=50;
}

void ASceneRandomizer::BeginPlay()
{
        Super::BeginPlay();

        // Randomize objects on game start
        RandomizeObjects();

        if (RANDOMIZER_PERIOD<=0)
            RANDOMIZER_PERIOD=50;
}

// Called every frame
void ASceneRandomizer::Tick(float DeltaTime)
{
        Super::Tick(DeltaTime);
        RANDOMIZER_TIMER=(RANDOMIZER_TIMER+1)%RANDOMIZER_PERIOD;
        if (RANDOMIZER_TIMER==0)
            RandomizeObjects();
}

void ASceneRandomizer::OnConstruction(const FTransform& Transform)
{
        Super::OnConstruction(Transform);

        // The `RandomizeObjects()` function is marked as `CallInEditor`, so it will be executed when
        // properties are changed in the editor.
}

void ASceneRandomizer::RandomizeObjects()
{
        // 1. Destroy any previously spawned actors to start from a clean slate.
        for (AActor* Actor : SpawnedActors)
        {
                if (Actor && !Actor->IsPendingKill())
                {
                        GetWorld()->DestroyActor(Actor);
                }
        }
        SpawnedActors.Empty();

        // 2. Spawn and configure each object based on the ObjectConfigs array.
        for (const FSceneObjectRandomizationConfig& Config : ObjectConfigs)
        {
                // Sanity check: Ensure there are meshes to choose from.
                if (Config.Meshes.Num() == 0)
                {
                        UE_LOG(LogTemp, Warning, TEXT("Object with ID '%s' has no meshes to randomize."), *Config.ObjectID.ToString());
                        continue;
                }

                // Randomly select a mesh and material from the available arrays.
                UStaticMesh* SelectedMesh = Config.Meshes[FMath::RandRange(0, Config.Meshes.Num() - 1)];
                UMaterialInterface* SelectedMaterial = nullptr;
                if (Config.Materials.Num() > 0)
                {
                        SelectedMaterial = Config.Materials[FMath::RandRange(0, Config.Materials.Num() - 1)];
                }

                // Calculate Gaussian-distributed mass and pose adjustment.
                const float RandomMass = GetGaussianRandom(Config.MassMean, Config.MassSigma);
                const FVector PositionAdjustment = FVector(
                        GetGaussianRandom(0.0f, Config.PoseAdjustmentSigma),
                        GetGaussianRandom(0.0f, Config.PoseAdjustmentSigma),
                        GetGaussianRandom(0.0f, Config.PoseAdjustmentSigma)
                );

                const FRotator RotationAdjustment = FRotator(
                        GetGaussianRandom(0.0f, Config.PoseAdjustmentSigma),
                        GetGaussianRandom(0.0f, Config.PoseAdjustmentSigma),
                        GetGaussianRandom(0.0f, Config.PoseAdjustmentSigma)
                );

                // Create the new pose by applying the random adjustment to the initial pose.
                const FVector NewLocation = Config.InitialPose.GetLocation() + PositionAdjustment;
                const FRotator NewRotation = Config.InitialPose.Rotator() + RotationAdjustment;
                const FTransform NewTransform(NewRotation, NewLocation, Config.InitialPose.GetScale3D());

                // Spawn a new actor and set up its components.
                FActorSpawnParameters SpawnParams;
                SpawnParams.Name = FName(*FString::Printf(TEXT("RandomizedObject_%s_%d"), *Config.ObjectID.ToString(), FMath::Rand()));
                AStaticMeshActor* NewActor = GetWorld()->SpawnActor<AStaticMeshActor>( AStaticMeshActor::StaticClass(),NewTransform, SpawnParams);
                if (NewActor)
                {
                        UStaticMeshComponent* MeshComponent =Cast<AStaticMeshActor>(NewActor)->GetStaticMeshComponent();
                        if (MeshComponent)
                        {
                                MeshComponent->UnregisterComponent();
                                MeshComponent->SetStaticMesh(SelectedMesh);
                                MeshComponent->SetMaterial(0, SelectedMaterial);
                                MeshComponent->SetMobility(EComponentMobility::Movable);
                                MeshComponent->SetMassOverrideInKg(NAME_None, RandomMass);
                                MeshComponent->SetSimulatePhysics(true); // Enable physics simulation
                                MeshComponent->SetEnableGravity(true);
                                MeshComponent->SetCollisionResponseToAllChannels(ECollisionResponse::ECR_Block);
                                MeshComponent->SetGenerateOverlapEvents(true);
                                MeshComponent->RegisterComponent();
                                //NewActor->SetRootComponent(MeshComponent);
                        }

                        SpawnedActors.Add(NewActor);
                }
        }

        // 3. Apply relationships between objects.
        for (const FSceneObjectRelationship& Relation : ObjectRelationships)
        {
                AActor* ActorA = FindActorByName(Relation.ObjectA);
                AActor* ActorB = FindActorByName(Relation.ObjectB);

                if (ActorA && ActorB)
                {
                        ApplyRelationship(ActorA, ActorB, Relation.RelationshipType);
                }
                else
                {
                        UE_LOG(LogTemp, Warning, TEXT("Failed to find one or both actors for relationship: %s, %s"), *Relation.ObjectA.ToString(), *Relation.ObjectB.ToString());
                }
        }
}

AActor* ASceneRandomizer::FindActorByName(FName InActorName) const
{
        for (AActor* Actor : SpawnedActors)
        {
                if (Actor && Actor->GetFName() == InActorName)
                {
                        return Actor;
                }
        }
        return nullptr;
}

void ASceneRandomizer::ApplyRelationship(AActor* ActorA, AActor* ActorB, EObjectRelationship Relation)
{
        if (!ActorA || !ActorB)
        {
                return;
        }

        FVector ActorBLocation = ActorB->GetActorLocation();
        FVector ActorBExtents = ActorB->GetRootComponent()->Bounds.BoxExtent;

        // This is a simplified implementation. For more complex/accurate physics relationships,
        // you would need to use physics constraints, joints, or more advanced collision checks.
        switch (Relation)
        {
        case EObjectRelationship::In:
        {
                // Position Actor A randomly within the bounding box of Actor B.
                const FVector RandomOffset = FVector(
                        FMath::FRandRange(-ActorBExtents.X, ActorBExtents.X),
                        FMath::FRandRange(-ActorBExtents.Y, ActorBExtents.Y),
                        FMath::FRandRange(-ActorBExtents.Z, ActorBExtents.Z)
                );
                ActorA->SetActorLocation(ActorBLocation + RandomOffset);
                break;
        }
        case EObjectRelationship::Left:
        {
                // Position Actor A to the left of Actor B by a small offset.
                const FVector NewLocation = ActorBLocation + FVector(0, -ActorBExtents.Y * 1.5f, 0);
                ActorA->SetActorLocation(NewLocation);
                break;
        }
        case EObjectRelationship::Right:
        {
                const FVector NewLocation = ActorBLocation + FVector(0, ActorBExtents.Y * 1.5f, 0);
                ActorA->SetActorLocation(NewLocation);
                break;
        }
        case EObjectRelationship::Front:
        {
                const FVector NewLocation = ActorBLocation + FVector(ActorBExtents.X * 1.5f, 0, 0);
                ActorA->SetActorLocation(NewLocation);
                break;
        }
        case EObjectRelationship::Back:
        {
                const FVector NewLocation = ActorBLocation + FVector(-ActorBExtents.X * 1.5f, 0, 0);
                ActorA->SetActorLocation(NewLocation);
                break;
        }
        case EObjectRelationship::Above:
        {
                const FVector NewLocation = ActorBLocation + FVector(0, 0, ActorBExtents.Z * 2.0f);
                ActorA->SetActorLocation(NewLocation);
                break;
        }
        case EObjectRelationship::Below:
        {
                const FVector NewLocation = ActorBLocation + FVector(0, 0, -ActorBExtents.Z * 2.0f);
                ActorA->SetActorLocation(NewLocation);
                break;
        }
        default:
                break;
        }

        // This is an important step. The physics engine needs to be reset for the new configuration
        // to take effect properly.
        UStaticMeshComponent* MeshComponent = Cast<UStaticMeshComponent>(ActorA->GetRootComponent());
        if (MeshComponent)
        {
                MeshComponent->SetSimulatePhysics(false);
                MeshComponent->SetSimulatePhysics(true);
        }
}

