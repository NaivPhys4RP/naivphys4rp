// Fill out your copyright notice in the Description page of Project Settings.


#include "NavierStockesServer.h"


        // Sets default values
        UNavierStockesServer::UNavierStockesServer()
        {
                this->U_Port=1005; // server port
                this->U_IpAddress=FString(TEXT("127.0.0.1")); //server ip
                this->U_IsConnected=false; //is server connected?
                this->U_Protocol=FString(TEXT("DEFAULT")); //protocol
                this->U_ServerInterface=NewObject<UUFluidParticle>();//server interface to particle
        }

        //destructor
        UNavierStockesServer::~UNavierStockesServer()
        {
        }


        //method members
        bool UNavierStockesServer::Start(){
              return false;
        }

        bool UNavierStockesServer::Pause(){
              return false;
        }

        bool UNavierStockesServer::Stop(){
              return false;
        }



