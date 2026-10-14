// Fill out your copyright notice in the Description page of Project Settings.

#pragma once
#include "Engine/SkeletalMesh.h"
#include "Animation/SkeletalMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "UObject/UObjectGlobals.h"
#include "Engine/World.h"
#include "UParaSimMonitor.h"
#include "GameFramework/Actor.h"
#include "CoreMinimal.h"

/**
 * By Kenghagho Kenfack
 * polyform can compound Actor
 */

UENUM()
enum ActorType
{
  SKELETAL_MESH     UMETA(DisplayName = "SKELETAL_MESH"),
  STATIC_MESH       UMETA(DisplayName = "STATIC_MESH"),
  VOLUME_MESH       UMETA(DisplayName = "VOLUME_MESH"),
};

class UPARASIM_API UParaSimActor
{
public:
	UParaSimActor();
	~UParaSimActor();

    ActorType Type;
    TArray<AUParaSimMonitor*> TVolumeActor;
    AUParaSimMonitor* VolumeActor;
    AStaticMeshActor* StaticMeshActor;
    TArray<AStaticMeshActor*> TStaticMeshActor;
    ASkeletalMeshActor* SkeletalMeshActor;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ore Types", meta = (AllowPrivateAccess = "true"))
    UStaticMesh* StaticMesh;
    bool PhysicsSimulation;
    UMaterial* Material;
    EComponentMobility::Type Mobility;
    FTransform Transform;
    FActorSpawnParameters* SpawnParameters;


    bool BuildActor(FName class_descriptor, FName material_descriptor, FRotator rotation,
                    FVector translation, FVector scale, EComponentMobility::Type mobility, bool physicsSimulation);

    bool BuildActor(UWorld* worldHandle);

    bool DeleteActor(UWorld* worldHandle);

    bool BuildActor_V2(UWorld* worldHandle);

    bool BuildActor_V3(UWorld* worldHandle, FVector translation, FRotator rotation,FString mesh_path, FString material_path,float mass);

    template <typename ObjClass>
    static FORCEINLINE ObjClass* LoadObjFromPath(const FName& Path);

    static FORCEINLINE UMaterial* LoadMaterialFromPath(const FName& Path);

    static FORCEINLINE UStaticMesh* LoadStaticMeshFromPath(const FName& Path);

};

