// Fill out your copyright notice in the Description page of Project Settings.

#pragma once
#include "Engine/SkeletalMesh.h"
#include "Animation/SkeletalMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "UObject/UObjectGlobals.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "CoreMinimal.h"
#include "UFluidParticle.generated.h"

/**
 * By Kenghagho Kenfack
 * polyform can compound Actor
 */

UENUM()
enum ParticleType
{
  P_SKELETAL_MESH     UMETA(DisplayName = "P_SKELETAL_MESH"),
  P_STATIC_MESH       UMETA(DisplayName = "P_STATIC_MESH"),
  P_VOLUME_MESH       UMETA(DisplayName = "P_VOLUME_MESH"),
};

UENUM()
enum ParticleState
{
  S_CREATED           UMETA(DisplayName = "S_CREATED"),
  S_BUILT             UMETA(DisplayName = "S_BUILT"),
  S_SPAWNED           UMETA(DisplayName = "S_SPAWNED"),
  S_TRANSITING        UMETA(DisplayName = "S_TRANSITING"),
  S_CONTAINED         UMETA(DisplayName = "S_CONTAINED"),
  S_MISSED            UMETA(DisplayName = "S_MISSED"),
  S_OVERFLOWED        UMETA(DisplayName = "S_OVERFLOWED"),
};

UCLASS()
class UFLUID_API UUFluidParticle: public UObject
{

    GENERATED_BODY()
public:
    
    UUFluidParticle();
    ~UUFluidParticle();

    //Unreal-Based Characterization

    ParticleState U_State;                        // Actor type

    ParticleType U_Type;                        // Actor type

    UWorld* U_WorldHandle;                      // World handle

    UMaterial* U_Material;  		// Materials for the actor in the given order

    UTexture2D* U_Texture;    		// Textures for the actor in the given order

    UPhysicalMaterial* U_PhysicalMaterial; 	// Physical materials

    AActor* U_VolumeActor;

    AStaticMeshActor* U_StaticMeshActor;

    ASkeletalMeshActor* U_SkeletalMeshActor;

    UStaticMesh* U_StaticMesh;

    bool U_PhysicsSimulation;

    bool U_GravityEnabled;

    EComponentMobility::Type U_Mobility;

    FTransform U_Transform;


    FActorSpawnParameters* U_SpawnParameters;

    //Semantics-Based Characterization

    UPROPERTY( )
    float CachedParticleSide = 0.8f;
    UPROPERTY( )
    float Mass;
    UPROPERTY( )
    FVector Scale;
    UPROPERTY( )
    float Density;
    UPROPERTY( )
    float Restitution;
    UPROPERTY( )
    float Friction;
    UPROPERTY( )
    float Volume;
    UPROPERTY( )
    float Viscosity;
    UPROPERTY( )
    FVector NS_Velocity;	//Navier-Stockes Velocity
    UPROPERTY( )
    float Linear_Damping;
    UPROPERTY( )
    float Angular_Damping;
    UPROPERTY( )
    float Destructibility;
    UPROPERTY( )
    FString Color;
    UPROPERTY( )
    FString Material;
    UPROPERTY( )
    FString Physical_Material;
    UPROPERTY( )
    FString Mesh;
    UPROPERTY( )
    bool IsAlive;
    UPROPERTY( )
    bool IsSpawned;
    UPROPERTY( )
    bool IsBuilt;
    UPROPERTY( )
    float Expected_Life_Time;
    UPROPERTY( )
    float Remaning_Life_Time;
    UPROPERTY( )
    FString Particle_Index;
    UPROPERTY( )
    FString Particle_Reference;

    //method members
    bool BuildParticle(UWorld* worldHandle,ParticleType type, FVector translation, FRotator rotation,
                       FVector scale,FString mesh_path, FString material_path, FString physical_material_path,float mass, float linear_damping, float angular_damping,float restitution, float friction, float density);
    bool SpawnParticle();
    bool UpdateParticle();
    bool DeleteParticle();
    bool WeakenParticle(float Impact);
    bool WeakenParticle();

    template <typename ObjClass>
    static FORCEINLINE ObjClass* LoadObjFromPath(const FName& Path);

    static FORCEINLINE UMaterial* LoadMaterialFromPath(const FName& Path);

    static FORCEINLINE UPhysicalMaterial* LoadPhysicalMaterialFromPath(const FName& Path);

    static FORCEINLINE UStaticMesh* LoadStaticMeshFromPath(const FName& Path);

};

