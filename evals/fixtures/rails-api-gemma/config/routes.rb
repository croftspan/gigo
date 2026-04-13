Rails.application.routes.draw do
  resources :users, only: [:index, :show, :create] do
    resources :orders, only: [:index, :show, :create]
  end
end
