<?php

namespace App\Filament\Pages;

use Filament\Pages\Dashboard as BaseDashboard;
use Illuminate\Support\Facades\Auth;

class Dashboard extends BaseDashboard
{
    protected static ?string $navigationLabel = 'Dasbor';

    public function getHeading(): string
    {
        $fullName = Auth::user()->name;
        $firstName = explode(' ', trim($fullName))[0];

        return 'Selamat datang, ' . $fullName . '.';
    }
}
