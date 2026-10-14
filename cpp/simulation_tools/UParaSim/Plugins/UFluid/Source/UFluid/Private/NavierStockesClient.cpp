// Fill out your copyright notice in the Description page of Project Settings.


#include "NavierStockesClient.h"


        // Sets default values
        UNavierStockesClient::UNavierStockesClient()
        {
                this->U_CPort=1005; // server port
                this->U_CIpAddress=FString(TEXT("127.0.0.1")); //server ip
                this->U_IsCConnected=false; //is server connected?
                this->U_CProtocol=FString(TEXT("DEFAULT")); //protocol
                this->U_ClientInterface=NewObject<UUFluidParticle>();//server interface to particle
        }

        //destructor
        UNavierStockesClient::~UNavierStockesClient()
        {
        }


        //method members
        bool UNavierStockesClient::Start(){
              return false;
        }

        bool UNavierStockesClient::Pause(){
              return false;
        }

        bool UNavierStockesClient::Send(){
              return false;
        }

        bool UNavierStockesClient::Receive(){
              return false;
        }

        bool UNavierStockesClient::Stop(){
              return false;
        }



