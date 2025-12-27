<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class ActivityType extends Model
{
    use HasFactory;

    public const REQUIRED_CATEGORY_PKKMB = 'PKKMB';
    public const REQUIRED_CATEGORY_BAKTI_LINGKUNGAN = 'BAKTI_LINGKUNGAN';

    protected $fillable = [
        'activity_field_id',
        'name',
        'level',
        'achievement',
        'score',
        'required_category',
    ];

    public function activityField(): BelongsTo
    {
        return $this->belongsTo(ActivityField::class);
    }
}
