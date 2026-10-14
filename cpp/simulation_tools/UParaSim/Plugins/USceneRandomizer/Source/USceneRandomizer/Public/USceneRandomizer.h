// Copyright 2025, Kenghagho Kenfack Franklin. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Engine/StaticMeshActor.h"
#include "USceneRandomizer.generated.h"

class UStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;

/** An enum to define the type of spatial relationship between two objects. */
UENUM(BlueprintType)
enum class EObjectRelationship : uint8
{
	None,
	In,
	Left,
	Right,
	Front,
	Back,
	Above,
	Below
};

/**
 * Configuration for a single object type to be randomized.
 * This struct allows you to define a pool of meshes and materials, as well as mass and pose properties.
 */
USTRUCT(BlueprintType)
struct FSceneObjectRandomizationConfig
{
	GENERATED_BODY()

	// A unique identifier for this object configuration.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Object Configuration")
	FName ObjectID;

	// The list of meshes that can be randomly selected for this object.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Object Configuration")
	TArray<UStaticMesh*> Meshes;

	// The list of materials that can be randomly selected for the chosen mesh.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Object Configuration")
	TArray<UMaterialInterface*> Materials;

	// The mean (mu) for the Gaussian distribution of the object's mass in kilograms.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Physics")
	float MassMean = 1.50f;

	// The standard deviation (sigma) for the Gaussian distribution of the object's mass.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Physics")
	float MassSigma = 1.0f;

	// The initial pose (location and rotation) of the object. Randomization will be applied around this pose.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Initial Pose")
	FTransform InitialPose;

	// The standard deviation for the Gaussian distribution of the pose adjustment.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pose Adjustment")
	float PoseAdjustmentSigma = 10.0f;
};

/**
 * Defines a spatial relationship between two objects.
 */
USTRUCT(BlueprintType)
struct FSceneObjectRelationship
{
	GENERATED_BODY()

	// The object that will be positioned based on the relation.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Relationships")
	FName ObjectA;

	// The object used as a reference for the relation.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Relationships")
	FName ObjectB;

	// The type of spatial relationship.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Relationships")
	EObjectRelationship RelationshipType = EObjectRelationship::None;
};


UCLASS(Blueprintable, hidecategories=(Physics, Rendering, Tags))
class USCENERANDOMIZER_API ASceneRandomizer : public AActor
{
	GENERATED_BODY()
	
public:	
	ASceneRandomizer();

	// Function to be called from the editor to trigger randomization.
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Randomizer")
	void RandomizeObjects();

protected:
	virtual void BeginPlay() override;
        // Called every frame
        virtual void Tick(float DeltaSeconds) override;
	virtual void OnConstruction(const FTransform& Transform) override;

private:
	/**
	 * Main configuration list for the randomization process.
	 * This list defines the objects to be spawned and their randomization properties.
	 */
	UPROPERTY(EditAnywhere, Category = "Randomizer Properties")
	TArray<FSceneObjectRandomizationConfig> ObjectConfigs;

	/**
	 * Defines relationships between objects that will influence their final positions.
	 * The relationships are applied after the initial randomization.
	 */
	UPROPERTY(EditAnywhere, Category = "Randomizer Properties")
	TArray<FSceneObjectRelationship> ObjectRelationships;

	// A list to hold the spawned actors for cleanup and relationships.
	UPROPERTY(Transient)
	TArray<AActor*> SpawnedActors;

        int RANDOMIZER_TIMER;

        UPROPERTY(EditAnywhere, Category = "Randomizer Properties")
        int RANDOMIZER_PERIOD;

	/**
	 * Helper function to find a spawned actor by its name.
	 * @param InActorName The name of the actor to find.
	 * @return A pointer to the found actor, or nullptr if not found.
	 */
	AActor* FindActorByName(FName InActorName) const;

	/**
	 * Helper function to apply the relationship between two actors.
	 * @param ActorA The actor to move.
	 * @param ActorB The reference actor.
	 * @param Relation The type of relationship.
	 */
	void ApplyRelationship(AActor* ActorA, AActor* ActorB, EObjectRelationship Relation);
};

