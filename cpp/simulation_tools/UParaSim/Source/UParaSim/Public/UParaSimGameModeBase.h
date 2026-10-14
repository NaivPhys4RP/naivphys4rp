// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "Engine/World.h"
#include "Math/UnrealMathUtility.h"
#include "Misc/App.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/GameModeBase.h"
#include "NavigationSystem.h"
#include "NavMesh/RecastNavMesh.h"
#include "UObject/UObjectHash.h"
#include "UParaSimActor.h"
#include "UParaSimGameModeBase.generated.h"

/**
 * 
 */
UCLASS()
class UPARASIM_API AUParaSimGameModeBase : public AGameModeBase
{
    GENERATED_BODY()
    public:

        //counter
        int counter;
        //constructor

        int port;

        int topic;

        AUParaSimGameModeBase();
        //list of maps to simulate.



        //UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="UParaSim Property")
        static TArray<FString> MapList;

        //active map. By default the first map in MapList is active
        //UPROPERTY(EditAnywhere, BlueprintReadWrite, Category= "UParaSim Property")
        static FString ActiveMap;

        //active map. By default the first map in MapList is active
        UPROPERTY(EditAnywhere, BlueprintReadWrite,Category="Particle Properties",meta = (AllowPrivateAccess = "true"))
        FString MapPath;

        static FString MainMap;

        //active world handle
        static UWorld* ActiveWorldHandle;

        //main world handle
        static UWorld* MainWorldHandle;

        //list of world handle
        static TArray<UWorld*> ListWorldHandles;

        //The number of maps to parallelize. By default only one map
        //UPROPERTY(EditAnywhere, BlueprintReadWrite, Category= "UParaSim Property")
        UPROPERTY(EditAnywhere, BlueprintReadWrite,Category="Particle Properties",meta = (AllowPrivateAccess = "true"))
        int NumberOfParticles;

        static int NumberOfMaps;

        //different handles
        static FDelegateHandle CleanupHandle;
        static FDelegateHandle TickHandle;

        //actor spawner
        UParaSimActor* ActorSpawner;

        //World context
        FWorldContext NewWorldContext;

        static TMap<UWorld*, FDelegateHandle> CleanupHandles;

        static TMap<UWorld*, FDelegateHandle> TickHandles;

        //load map error
        FString loadError;

        // Called when the game starts or when spawned
        virtual void BeginPlay() override;

        // Called every frame
        virtual void Tick(float DeltaTime) override;

        UWorld* GetThisWorldHandle();

        UWorld* GetActiveWorldHandle();

        static UWorld* GetMainWorldHandle();

        bool SwitchWorld(UWorld* TargetWorld);

        bool LoadWorld(FString TargetWorldMap);

        bool LoadWorldAsync(FString TargetWorldMap);

        bool SetShouldTickWhenInBackground(UWorld* TargetWorld, bool value);

        bool EndWorld(UWorld* TargetWorld);

        bool SpawnActor(UParaSimActor* TargetActor);

        bool DeleteActor(UParaSimActor* TargetActor);

        UWorld* CreateNewWorld(FString map_name);

        UWorld* CreateNewWorld(FString map_name, TSubclassOf<class AGameModeBase> GameMode);

        void ToColorImage( TArray<FColor> &ImageData, uint8 *Bytes);

        void ReadColorImage(UTextureRenderTarget2D *RenderTarget, TArray<FColor> &ImageData);

        void SavePng(UTextureRenderTarget2D* RenderTarget,TArray<FColor> Image, FString Filename);
};
