// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Camera/CameraActor.h"
#include "GameFramework/SpringArmComponent.h"
#include "Components/SceneComponent.h"
#include "Math/UnrealMathUtility.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Camera/CameraComponent.h"
#include "UFluidParticle.h"
#include "UFluidSmartSource.h"
#include "SceneManagement.h"
#include "Components/LineBatchComponent.h"
#include "UFluidHUD.h"
#include "ProceduralMeshComponent.h" // <-- Added for 3D visual geometry generation
#include "UFluidSample.generated.h"

USTRUCT(BlueprintType)
struct FHumanMotionStep
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Human Motion")
    int32 Iteration = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Human Motion")
    float CumulativeX = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Human Motion")
    float CumulativeY = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Human Motion")
    float CumulativeZ = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Human Motion")
    float CumulativeTheta = 0.0f;
};


struct FL0OrientedBox
{
    FVector Center;

    FVector Forward;
    FVector Right;
    FVector Up;

    FL0OrientedBox()
        : Center(0.0f, 0.0f, 0.0f),
          Forward(0.0f, 0.0f, 0.0f),
          Right(0.0f, 0.0f, 0.0f),
          Up(0.0f, 0.0f, 0.0f)
    {
    }
};


UENUM()
enum FluidState
{
  FS_CREATED          UMETA(DisplayName = "FS_CREATED"),
  FS_FILLING          UMETA(DisplayName = "FS_FILLING"),
  FS_POURING          UMETA(DisplayName = "FS_POURING"),
};

UCLASS()
class UFLUID_API AUFluidSample : public AActor
{
    GENERATED_BODY()

public:
     // Sets default values for this pawn's properties
     AUFluidSample();
     ~AUFluidSample();
    /** Camera boom positioning the camera behind the fluid */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Fluid Camera", meta = (AllowPrivateAccess = "true"))
    class USpringArmComponent* U_CameraBoom;

    /** Follow camera observing the fluid */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fluid Camera", meta = (AllowPrivateAccess = "true"))
    class UFluidSceneCaptureComponent2D* U_FollowCamera;

    /** Fluid emitter */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fluid Emitter", meta = (AllowPrivateAccess = "true"))
    class UUFluidEmitter* U_FluidEmitter;

    /** Fluid Main Container */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fluid Main Container", meta = (AllowPrivateAccess = "true"))
    class AUFluidSmartSource* U_FluidMainContainer;

    /** Fluid Main Container */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fluid Main Container", meta = (AllowPrivateAccess = "true"))
    class AUFluidSmartSource* U_FluidDestinationContainer;

    /** Fluid HUD */
    //UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fluid HUD", meta = (AllowPrivateAccess = "true"))
    //class AHUD* U_FluidHUD;

    /** Prevent the execution of tick without completion of begin play */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fluid Execution Flow Control", meta = (AllowPrivateAccess = "true") )
    bool U_ShouldBegin;

    /** Actual handle of the world in which the fluid operates */
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Execution Flow Control", meta = (AllowPrivateAccess = "true"))
    UWorld* U_WorldHandle;                      // World handle


    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Event", meta = (AllowPrivateAccess = "true"))
    TEnumAsByte<FluidState> U_FluidState;

    //Fluid's Physical Model
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    FRotator U_FluidOrientation;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    FVector U_FluidPosition;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    FVector U_ParticleScale;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    float U_FluidMass;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    float U_FluidDensity;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    float U_FluidRestitution;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    float U_FluidFriction;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    float U_FluidVolume;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    float U_FluidViscosity;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    FVector U_FLuid_NS_Velocity;	//Navier-Stockes Velocity
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    float U_FluidLinearDamping;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    float U_FluidAngularDamping;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    float U_FluidDestructibility;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    FString U_FluidColor;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    FString U_FluidMaterial;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    bool U_IsSampleFromVolume;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    bool U_FluidNumberParticle;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    float U_FluidExpectedLifeTime;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    float U_FluidRemaningLifeTime;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    int U_NumberParticles;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    float U_CovalentBond;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    float U_CovalentBondTickness;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    float U_CovalentBondForce;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    bool U_Color;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    UStaticMesh* U_FluidMesh;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    UMaterial* U_Material;  		// Materials for the actor in the given order
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    UPhysicalMaterial* U_PhysicalMaterial; 	// Physical materials
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    FColor Sample_Color;
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Physical Model", meta = (AllowPrivateAccess = "true"))
    FLinearColor Test_Color;
    bool Should_Use_Fluid;


    // Line Batch Component
    UPROPERTY( EditAnywhere, BlueprintReadWrite, Category = "Fluid Mesh", meta = (AllowPrivateAccess = "true"))
    class ULineBatchComponent* LineBatcher;

    // 3D Procedural Mesh Component (replaces legacy Line drawing / Debug drawing)
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Fluid Graphics")
    UProceduralMeshComponent* FluidMeshComponent; // <-- Added component pointer

    TArray<FVector> Points;
    TArray<FVector> Vertices;
    TArray<int32> Indices;
    //  Array Of indices that map to groups of lines in Points array
    TArray<int32> DrawGroupIndices;


    // Array Storing lines to be drawn
    TArray<FBatchedLine> Lines;


protected:
    // Called when the game starts or when spawned SCS_SceneColorHDR,
    virtual void BeginPlay() override;

public:
    // Called every frame
    virtual void Tick(float DeltaTime) override;

    // Called to bind functionality to input
        //virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

        //delete sample
        bool DeleteSample();

        // --- Runtime Telemetry Flags ---
        UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Fluid | Telemetry")
        float bIsSpilledFlag = 0.0f;

        UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Fluid | Telemetry")
        float bIsOverflowFlag = 0.0f;

        UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Fluid | Telemetry")
        float CachedTipOver = 0.0f;

        UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Fluid | Telemetry")
        float CachedOccupancy = 0.0f;

        UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Fluid | Telemetry")
        float CachedFlowTime = 0.0f;

        UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Fluid | Telemetry")
        float CachedSpreadArea = 0.0f;

        UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Fluid | Telemetry")
        float CachedTargetVolume = 0.0f;

        //update sample id state on hud
        UFUNCTION(BlueprintCallable, Category = "UFluid HUD Update")
        FText UpdateFluidIDHUD();

        UFUNCTION(CallInEditor, Category = "Fluid | Telemetry")
        void saveSignal();


        //update sample state on hud
        UFUNCTION(BlueprintCallable, Category = "UFluid HUD Update")
        float UpdateSampleHUD();

        //update escaped sample state on hud
        UFUNCTION(BlueprintCallable, Category = "UFluid HUD Update")
        float UpdateEscapedHUD();

        //update escaped sample state on hud
        UFUNCTION(BlueprintCallable, Category = "UFluid HUD Update")
        bool UpdateMissDetectedHUD();

        //update spillage sample state on hud
        UFUNCTION(BlueprintCallable, Category = "UFluid HUD Update")
        bool UpdateSpillageDetectedHUD();

        //update escaped sample state on hud
        UFUNCTION(BlueprintCallable, Category = "UFluid HUD Update")
        bool UpdateOverflowDetectedHUD();

        //compute container bounding box
        FL0OrientedBox CalculateActorOrientedBoundingBox(AUFluidSmartSource* Container);

        //draw oriented bounding box
        bool DrawDebugOrientedBox(UWorld* World, const FL0OrientedBox& Box, const FColor& Color,float LifeTime, FVector TargetParticle);

        //build fluid mesh
        bool BuildFluidMesh();

        //amount of fluid escaped
        float QUANTITY_ESCAPED;

        //estimate fluild spread area
        float EstimateSpreadArea(float ThresholdPercent, float ThresholdDistance);

        //estimate the occupied area by a fluid
        float CalculateProjectedOccupiedArea();

        //check if a point lies in OBB

        bool IsPointInsideOOB(const FL0OrientedBox& Box, const FVector& Point);

        UFUNCTION(CallInEditor, Category = "Fluid | HumanManipulation")
        void Manipulate();

        UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Fluid | HumanManipulation")
        float Delta_Orientation = 1.0f;

        UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Fluid | HumanManipulation")
        float Delta_Position = 1.0f;

        UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Fluid | HumanManipulation")
        int32 Current_Index = 0;

        UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Fluid | HumanManipulation")
        TArray<FHumanMotionStep> HumanMotionTrajectory;

        private:
            bool bIsTrajectoryLoaded = false;
            void LoadMotionTrajectory();

            // Add these to your class member variables:
            FTransform InitialContainerTransform;
            bool bIsInitialTransformSaved = false;
};
