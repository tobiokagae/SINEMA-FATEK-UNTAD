<?php

namespace App\Models;

use Filament\Models\Contracts\FilamentUser;
use Filament\Models\Contracts\HasAvatar;
use Filament\Panel;
use Illuminate\Contracts\Auth\MustVerifyEmail;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Relations\HasOne;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

class User extends Authenticatable implements FilamentUser, MustVerifyEmail, HasAvatar
{
    use HasFactory, Notifiable;

    protected $fillable = ['name', 'email', 'password', 'role'];
    protected $hidden = ['password', 'remember_token'];

    protected function casts(): array
    {
        return ['email_verified_at' => 'datetime', 'password' => 'hashed'];
    }

    public function student(): HasOne
    {
        return $this->hasOne(Student::class);
    }

    public function canAccessPanel(Panel $panel): bool
    {
        // Sesuaikan logika ini jika perlu
        // return str_ends_with($this->email, '@untad.ac.id') && $this->hasVerifiedEmail();
        return true;
    }

    // Metode untuk avatar (opsional)
    public function getFilamentAvatarUrl(): ?string
    {
        // Contoh menggunakan Gravatar
        return 'https://www.gravatar.com/avatar/' . md5(strtolower(trim($this->email)));
    }
}
