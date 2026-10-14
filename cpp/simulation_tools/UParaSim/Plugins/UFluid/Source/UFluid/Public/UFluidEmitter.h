// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerState.h"
#include "UFluidParticle.h"
#include "UFluidEmitter.generated.h"

/**
 * @author: Kenghagho Kenfack Franklin
 */
 
UCLASS()
class UFLUID_API UUFluidEmitter: public UObject
{

    GENERATED_BODY()
	public:

                UUFluidEmitter();
                UUFluidEmitter(UWorld* worldHandle, TArray<UUFluidParticle*> ListParticles);
                ~UUFluidEmitter();

                UPROPERTY()
		int U_NumberParticles; //how many to emit in number of particles
                UPROPERTY()
                float U_SampleVolume; //volume of sample
                UPROPERTY()
		bool U_InVolume; //how much to emit in volume
                UPROPERTY( )
                bool U_IsPaused; //
                UPROPERTY( )
                int U_EmissionRate; //how many to emit per clock
                UPROPERTY()
                class UUFluidParticle* U_ParticleModel; //particle model
                UPROPERTY( )
                UWorld* U_WorldHandle;                      // World handle
                /* Particle Model */
                UPROPERTY( )
                TArray<UUFluidParticle*> U_FluidParticles;

                bool U_Color;
                bool Fluid_Created;
		
		//method
                bool StartEmission(FTransform SampleTransform);
		bool PauseEmission();
		bool StopEmission();
		
};
