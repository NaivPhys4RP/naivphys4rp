#ifndef SMARTFLUIDSOURCE_H
#define SMARTFLUIDSOURCE_H

#endif // SMARTFLUIDSOURCE_H

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
#include "UFluidSmartSource.generated.h"

/**
 * By Kenghagho Kenfack
 * polyform can compound Actor
 */

UENUM()
enum SourceType
{
  S_SKELETAL_MESH     UMETA(DisplayName = "S_SKELETAL_MESH"),
  S_STATIC_MESH       UMETA(DisplayName = "S_STATIC_MESH"),
  S_VOLUME_MESH       UMETA(DisplayName = "S_VOLUME_MESH"),
};

UCLASS()
class UFLUID_API AUFluidSmartSource: public AStaticMeshActor
{

    GENERATED_BODY()
public:

    AUFluidSmartSource();
    ~AUFluidSmartSource();

    // Called when the game starts or when spawned
    virtual void BeginPlay() override;

    // Called every frame
    virtual void Tick(float DeltaSeconds) override;

    // Control the container
    bool Control();

    // Control parameters
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Source Control Parameters ", meta = (AllowPrivateAccess = "true"))
    float Delta_Position;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Source Control Parameters ", meta = (AllowPrivateAccess = "true"))
    float Delta_Orientation ;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Source Control Parameters", meta = (AllowPrivateAccess = "true"))
    FVector ContainerNormal = FVector(0.0f, 0.0f, 1.0f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Source Control Parameters", meta = (AllowPrivateAccess = "true"))
    FVector BoundaryOffset = FVector(0.0f, 0.0f, 0.0f);

    // Control commands
    UPROPERTY(EditAnywhere,  BlueprintReadWrite, Category = " Source Control Commands", meta = (AllowPrivateAccess = "true"))
    bool Move_Up;

    UPROPERTY(EditAnywhere,  BlueprintReadWrite, Category = " Source Control Commands", meta = (AllowPrivateAccess = "true"))
    bool Move_Down;

    UPROPERTY(EditAnywhere,  BlueprintReadWrite, Category = " Source Control Commands", meta = (AllowPrivateAccess = "true"))
    bool Move_Front;

    UPROPERTY(EditAnywhere,  BlueprintReadWrite, Category = " Source Control Commands", meta = (AllowPrivateAccess = "true"))
    bool Move_Back;

    UPROPERTY(EditAnywhere,  BlueprintReadWrite, Category = " Source Control Commands", meta = (AllowPrivateAccess = "true"))
    bool Move_Left;

    UPROPERTY(EditAnywhere,  BlueprintReadWrite, Category = " Source Control Commands", meta = (AllowPrivateAccess = "true"))
    bool Move_Right;

    UPROPERTY(EditAnywhere,  BlueprintReadWrite, Category = " Source Control Commands", meta = (AllowPrivateAccess = "true"))
    bool Rotate_Right;

    UPROPERTY(EditAnywhere,  BlueprintReadWrite, Category = " Source Control Commands", meta = (AllowPrivateAccess = "true"))
    bool Rotate_Left;

    UPROPERTY(EditAnywhere,  BlueprintReadWrite, Category = " Source Control Commands", meta = (AllowPrivateAccess = "true"))
    bool Rotate_Up;

    UPROPERTY(EditAnywhere,  BlueprintReadWrite, Category = " Source Control Commands", meta = (AllowPrivateAccess = "true"))
    bool Rotate_Down;

    UPROPERTY(EditAnywhere,  BlueprintReadWrite, Category = " Source Control Commands", meta = (AllowPrivateAccess = "true"))
    bool Tilt_Right;

    UPROPERTY(EditAnywhere,  BlueprintReadWrite, Category = " Source Control Commands", meta = (AllowPrivateAccess = "true"))
    bool Tilt_Left;

};

