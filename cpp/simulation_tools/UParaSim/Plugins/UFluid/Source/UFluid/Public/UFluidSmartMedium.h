#ifndef UFLUIDSMARTMEDIUM_H
#define UFLUIDSMARTMEDIUM_H

#endif // UFLUIDSMARTMEDIUM_H


// Fill out your copyright notice in the Description page of Project Settings.

#pragma once
#include "Engine/SkeletalMesh.h"
#include "Animation/SkeletalMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "UObject/UObjectGlobals.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "UFluidSample.h"
#include "CoreMinimal.h"
#include "UFluidSmartMedium.generated.h"

/**
 * By Kenghagho Kenfack
 * polyform can compound Actor
 */

UENUM()
enum MediumType
{
  M_SKELETAL_MESH     UMETA(DisplayName = "M_SKELETAL_MESH"),
  M_STATIC_MESH       UMETA(DisplayName = "M_STATIC_MESH"),
  M_VOLUME_MESH       UMETA(DisplayName = "M_VOLUME_MESH"),
};

UCLASS()
class UFLUID_API AUFluidSmartMedium: public AStaticMeshActor
{

    GENERATED_BODY()
public:

    AUFluidSmartMedium();
    ~AUFluidSmartMedium();
   TArray<FVector> Force_Field;
   TArray<int> Selected_Target_Particles;

    // Called when the game starts or when spawned
    virtual void BeginPlay() override;

    // Called every frame
    virtual void Tick(float DeltaSeconds) override;

   // Transport fluid
   bool BuildForceField();

   //compute distance of a point to tube axis
   float DistanceToMedium(FVector A, FVector B, FVector C);

   // Transport fluid
   bool BuildForceField_V2();

    // Transport fluid
    bool Transport();
    bool Reverse_Status;
    int force_field_trajectory_pointer;

    // Control parameters
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Medium Transport Parameters ", meta = (AllowPrivateAccess = "true"))
    float Force_Field_Intensity;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Medium Transport Parameters ", meta = (AllowPrivateAccess = "true"))
    float Intensity_Multiplier;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Medium Transport Parameters ", meta = (AllowPrivateAccess = "true"))
    float Intensity_Treshold;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Medium Transport Parameters ", meta = (AllowPrivateAccess = "true"))
    float Force_Field_Angle;


    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Medium Transport Parameters ", meta = (AllowPrivateAccess = "true"))
    float Force_Field_Area_Density;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Medium Transport Parameters ", meta = (AllowPrivateAccess = "true"))
    int Force_Field_Volume_Density;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Medium Transport Parameters ", meta = (AllowPrivateAccess = "true"))
    float Force_Field_Treshold;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Medium Transport Parameters ", meta = (AllowPrivateAccess = "true"))
    bool Should_Reverse_Force_Field;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Medium Transport Parameters ", meta = (AllowPrivateAccess = "true"))
    TArray<FVector> Force_Field_Trajectory;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Medium Transport Parameters ", meta = (AllowPrivateAccess = "true"))
    bool Should_Transport;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Medium Transport Parameters ", meta = (AllowPrivateAccess = "true"))
    bool Should_Show_Force_Field;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Medium Transport Parameters ", meta = (AllowPrivateAccess = "true"))
    float Force_Vector_Thickness;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Medium Transport Parameters ", meta = (AllowPrivateAccess = "true"))
    float Force_Vector_Arrow_Size;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = " Trandported Fluid ", meta = (AllowPrivateAccess = "true"))
    AUFluidSample* TargetFluid;

};

