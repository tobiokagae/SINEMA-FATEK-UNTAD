<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Signatory extends Model
{
    protected $fillable = [
        'name',
        'nip',
        'jabatan',
        'pangkat',
        'golongan',
        'signature_image_path',
        'stamp_image_path',
        'faculty_id',
    ];

    public function faculty(): BelongsTo
    {
        return $this->belongsTo(Faculty::class);
    }
}
