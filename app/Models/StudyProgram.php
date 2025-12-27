<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class StudyProgram extends Model
{
    protected $guarded = [];

    public function faculty(): BelongsTo
    {
        return $this->belongsTo(Faculty::class);
    }
}
