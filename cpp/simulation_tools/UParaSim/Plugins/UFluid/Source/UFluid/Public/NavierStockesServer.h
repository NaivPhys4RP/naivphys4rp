// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerState.h"
#include "UFluidParticle.h"
#include "NavierStockesServer.generated.h"

/**
 * @author: Kenghagho Kenfack Franklin
 */

UCLASS()
class UFLUID_API UNavierStockesServer: public UObject
{

    GENERATED_BODY()
        public:

                UNavierStockesServer();
                ~UNavierStockesServer();

                UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = Camera, meta = (AllowPrivateAccess = "true"))
                int U_Port; //connection port between deep learning models and unreal NS server
                UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = Camera, meta = (AllowPrivateAccess = "true"))
                FString U_IpAddress; //ip adress of server
                UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = Camera, meta = (AllowPrivateAccess = "true"))
                bool U_IsConnected; //is server connected
                UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = Camera, meta = (AllowPrivateAccess = "true"))
                FString  U_Protocol; //server protocol
                class UUFluidParticle* U_ServerInterface; //server interface to particle

                //method
                bool Start();
                bool Pause();
                bool Stop();

};
