<?php

namespace App\Providers;

use Illuminate\Foundation\Support\Providers\RouteServiceProvider as ServiceProvider;
use Illuminate\Support\Facades\Route;

class AuthRouteServiceProvider extends ServiceProvider
{
    /**
     * Bootstrap services.
     */
    public function boot(): void
    {
        $this->routes(function () {
            Route::middleware('web') // Penting! Gunakan middleware 'web'
                ->group(base_path('routes/auth.php'));
        });
    }
}
