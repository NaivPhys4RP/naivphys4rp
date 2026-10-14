// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Animation/WidgetAnimation.h"
#include "Blueprint/UserWidget.h"
#include "Components/TextBlock.h"
#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
#include "Core.h"
#include "Widgets/SCompoundWidget.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Framework/Commands/Commands.h"
#include "UnrealClient.h"
#include "Styling/SlateStyle.h"
#include "UObject/ObjectMacros.h"
#include "Runtime/Slate/Public/Widgets/Input/SComboBox.h"
#include "Application/SlateApplicationBase.h"
//#include "CommonGameViewportClient.h"
#include "GameFramework/HUD.h"
#include "UParaSimHUD.generated.h"

class SWindow;
class SViewport;
class FSceneViewport;
class UTextureRenderTarget2D;
/**
 *By Kenghagho
 */

/*       *********************************************************************************** */

class UPARASIM_API IUParaSimScene : public IModuleInterface
{
public:

    /**
     * Singleton-like access to this module's interface.  This is just for convenience!
     * Beware of calling this during the shutdown phase, though.  Your module might have been unloaded already.
     *
     * @return Returns singleton instance, loading the module on demand if needed
     */
    static inline IUParaSimScene& Get()
    {
        return FModuleManager::LoadModuleChecked< IUParaSimScene >("UParaSim");
    }

    /**
     * Checks to see if this module is loaded and ready.  It is only valid to call Get() if IsAvailable() returns true.
     *
     * @return True if the module is loaded and ready to use
     */
    static inline bool IsAvailable()
    {
        return FModuleManager::Get().IsModuleLoaded("UParaSim");
    }


public:
    /**
    * Get pointer to Texture render target
    * To make sure UTextureRenderTarget2D lifetime is controlled elsewhere, use "weak" ptr.
    * This is abstract fucntion and it need to be implemened
    */
     virtual TWeakObjectPtr<UTextureRenderTarget2D> GetTextureRenderTarget2D(int ID) =0;

    /**
    * Set UTextureRenderTarget2D to TWeakObjectPtr
    * This is abstract fucntion and it need to be implemened
    */

    virtual void SetTextureRenderTarget2D(UTextureRenderTarget2D* TexRenderTarget2D) =0;

};









/*       *********************************************************************************** */

UCLASS(hidecategories = (Collision, Object, Physics, SceneComponent), ClassGroup = Rendering, editinlinenew, meta = (BlueprintSpawnableComponent))
class UPARASIM_API UUParaSimSceneCaptureComponent2D : public USceneCaptureComponent2D
{
    GENERATED_BODY()

public:
    virtual void Activate(bool bReset) override;

#if WITH_EDITOR
    virtual void OnRegister() override;
#endif

};




/*       *********************************************************************************** */


/**
* Custom Viewport client, where we have access to canvas on Draw function.
* This is the place where we issue canvas draw call to present SceneCaptureComponent Texture to custom window
*/

class FUParaSimViewportClient : public FViewportClient
{
public:
    /** FViewportClient interface */
    /**
    * Execute Draw each tick
    * This is the place for issue draw cumments and start rendering
    */
    FUParaSimViewportClient(int slate_ID);
    virtual void Draw(FViewport* Viewport, FCanvas* Canvas) override;
    virtual bool InputKey(FViewport* Viewport, int32 ControllerId, FKey Key, EInputEvent Event, float AmountDepressed = 1.0f, bool bGamepad = false) override;
    virtual bool InputAxis(FViewport* Viewport, int32 ControllerId, FKey Key, float Delta, float DeltaTime, int32 NumSamples = 1, bool bGamepad = false) override;
    virtual bool InputGesture(FViewport* Viewport, EGestureEvent GestureType, const FVector2D& GestureDelta, bool bIsDirectionInvertedFromDevice) override;
    virtual UWorld* GetWorld() const override { return nullptr; }
    virtual void RedrawRequested(FViewport* Viewport) override { Viewport->Draw(); }
    int Slate_ID;
};

/**
 * Implements the Play Capture viewport
 */

class SUParaSimViewport : public SCompoundWidget
{
public:

    SLATE_BEGIN_ARGS(SUParaSimViewport)
    :_CWORLD(nullptr),
    _slate_ID(0)
    { }
    SLATE_ATTRIBUTE(UWorld*, CWORLD)
    SLATE_ATTRIBUTE(int, slate_ID)
    SLATE_END_ARGS()

public:
    void Construct(const FArguments& InArgs);

private:
    TSharedPtr<SViewport> Viewport;
    TSharedPtr<FSceneViewport> SceneViewport;
    TSharedPtr<FUParaSimViewportClient> PlaySceneViewportClient;

public:
    // SWidget overrides
    /**
    * Tick each engine tick, this is where we call FViewport::Draw() --> FUParaSimViewportClient::Draw(...)
    */
    virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override;

};

/**
* This is main container class, which is create Play Capture Window
* And it assign rendering Viewport for the Window
*/

class  UUParaSimSceneSlate
{

public:
    UUParaSimSceneSlate(UWorld* cworld, int ID);
    ~UUParaSimSceneSlate();

public:
    static void Initialize(UWorld* cworld);
    static void Shutdown();
    int Slate_ID;
    static int NBR_OF_PARTICLES;
private:
    TSharedPtr<SWindow> PlaySceneWindow;
    int PlaySceneWindowWidth;
    int PlaySceneWindowHeight;
    FOnWindowClosed InDelegate;

private:
    /**
    * Destroy window and all rendering viewports when window has been closed
    */
    void OnWindowClosed(const TSharedRef<SWindow>& Window);

private:
    TSharedPtr<SUParaSimViewport> PlaySceneViewport;
    static TArray<TSharedPtr<UUParaSimSceneSlate>> PlaySceneSlate;
    static bool RUNNING;
};



/*
UCLASS()
class UPARASIM_API UUParaSimCommonGameViewportClient : public UCommonGameViewportClient
{

    GENERATED_BODY()

    public:

    void ChangeRenderWorld(UWorld* NewWorld) { World = NewWorld; }

};
*/




/*       *********************************************************************************** */
UCLASS()
class UPARASIM_API UUParaSimWidget : public UUserWidget
{
  GENERATED_BODY()

    public:

        UUParaSimWidget(const FObjectInitializer& ObjectInitializer);

        virtual void NativeConstruct() override;

        UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (BindWidget))
        class UTextBlock* TXTCombo;

        void UpdateComboCount(int32 Value);

        void ResetCombo();

        void StoreWidgetAnimations();

        UWidgetAnimation* GetAnimationByName(FName AnimationName) const;

    private:

        TMap<FName, UWidgetAnimation*> AnimationsMap;

        UWidgetAnimation* ComboFadeAnimation;

        UWidgetAnimation* ComboShakeAnimation;
};


/*       *********************************************************************************** */


UCLASS()
class UPARASIM_API AUParaSimHUD : public AHUD
{
	GENERATED_BODY()

    public:

        AUParaSimHUD(const FObjectInitializer& ObjectInitializer);

        // Primary draw call for the HUD.
        virtual void DrawHUD() override;

        virtual void BeginPlay() override;

        virtual void Tick(float DeltaSeconds) override;

        UFUNCTION()
        void UpdateComboCount(int32 Value);

        UFUNCTION()
        void ResetCombo();

        UPROPERTY(EditDefaultsOnly, Category = "Interactive")
        TSubclassOf<UUserWidget> HitComboWidgetClass;

    private:

        UUParaSimWidget* HitComboWidget;
	
	
};

/*       *********************************************************************************** */

class FUParaSimSceneStyle
{
public:

    static void Initialize();

    static void Shutdown();

    /** reloads textures used by slate renderer */
    static void ReloadTextures();

    /** @return The Slate style set for the Shooter game */
    static const ISlateStyle& Get();

    static FName GetStyleSetName();

private:

    static TSharedRef< class FSlateStyleSet > Create();

private:

    static TSharedPtr< class FSlateStyleSet > StyleInstance;
};

/*       *********************************************************************************** */

class FUParaSimSceneCommands : public TCommands<FUParaSimSceneCommands>
{
public:

    FUParaSimSceneCommands()
        : TCommands<FUParaSimSceneCommands>(TEXT("UParaSim"), NSLOCTEXT("Contexts", "UParaSim", "UParaSim Plugin"), NAME_None, FUParaSimSceneStyle::GetStyleSetName())
    {
    }

    // TCommands<> interface
    virtual void RegisterCommands() override;

public:
    TSharedPtr< FUICommandInfo > OpenPluginWindow;
};
