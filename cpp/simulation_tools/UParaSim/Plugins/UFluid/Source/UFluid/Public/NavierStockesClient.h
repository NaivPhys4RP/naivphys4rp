// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerState.h"
#include "UFluidParticle.h"
#include "NavierStockesClient.generated.h"

/**
 * @author: Kenghagho Kenfack Franklin
 */

UCLASS()
class UFLUID_API UNavierStockesClient: public UObject
{

    GENERATED_BODY()
        public:

                UNavierStockesClient();
                ~UNavierStockesClient();

                UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = Camera, meta = (AllowPrivateAccess = "true"))
                int U_CPort; //connection port between deep learning models and unreal NS client
                UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = Camera, meta = (AllowPrivateAccess = "true"))
                FString U_CIpAddress; //ip adress of client
                UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = Camera, meta = (AllowPrivateAccess = "true"))
                bool U_IsCConnected; //is client connected
                UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = Camera, meta = (AllowPrivateAccess = "true"))
                FString  U_CProtocol; //client protocol
                class UUFluidParticle* U_ClientInterface; // client interface to particle

                //method
                bool Start();
                bool Pause();
                bool Send();
                bool Receive();
                bool Stop();

};
